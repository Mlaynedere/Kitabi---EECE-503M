from flask import Blueprint, render_template, flash, redirect, request, jsonify, url_for
from flask_login import login_required, current_user
from .models import Customer, Product, Order, Return, Cart, Category, SubCategory
from . import db
from intasend import APIService
from .forms import CustomerReturnForm
from .utils import get_categories_dict

views = Blueprint('views', __name__)

API_PUBLISHABLE_KEY = 'ISPubKey_test_f89875d2-8db8-434b-864d-3ebc564d7afd'

API_TOKEN = 'ISSecretKey_test_be2d57dd-b5f6-47de-9b8a-24120ff8965c'

from flask import redirect, url_for
from flask_login import current_user

@views.route('/')
def home():
    if current_user.is_authenticated and (current_user.is_admin):
        return redirect(url_for('admin.admin_page'))
    
    items = Product.query.all()
    cart_items = {
        item.product_link: item 
        for item in Cart.query.filter_by(customer_link=current_user.id).all()
    } if current_user.is_authenticated else {}
    
    return render_template('home.html',
                         items=items,
                         cart=Cart.query.filter_by(customer_link=current_user.id).all() if current_user.is_authenticated else [],
                         cart_items=cart_items,
                         categories=get_categories_dict())

@views.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    item_to_add = Product.query.get(item_id)
    # Get the product's stock
    product_stock = item_to_add.in_stock

    # Get the current quantity of this item in the user's cart
    current_cart_item = Cart.query.filter_by(product_link=item_id, customer_link=current_user.id).first()

    if current_cart_item:
        # Check if the user is trying to add more than available stock
        if current_cart_item.quantity >= product_stock:
            flash(f'You cannot add more than {product_stock} of {item_to_add.product_name} to your cart as it is out of stock.', 'error')
            return redirect(request.referrer)

        # Increase the quantity by 1
        current_cart_item.quantity += 1
    else:
        # Add new cart item if it's not already in the cart
        if product_stock > 0:
            new_cart_item = Cart()
            new_cart_item.quantity = 1
            new_cart_item.product_link = item_to_add.id
            new_cart_item.customer_link = current_user.id

            db.session.add(new_cart_item)
        else:
            flash(f'{item_to_add.product_name} is out of stock and cannot be added to your cart.', 'error')
            return redirect(request.referrer)

    # Commit the changes to the database
    try:
        db.session.commit()
        flash(f'{item_to_add.product_name} added to your cart', 'success')
    except Exception as e:
        print('Error adding item to cart:', e)
        flash('There was an error adding the item to your cart', 'error')

    return redirect(request.referrer)

@views.route('/cart')
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = 0
    for item in cart:
        amount += item.product.current_price * item.quantity

    return render_template('cart.html', 
                         cart=cart, 
                         amount=amount, 
                         total=amount+3,
                         categories=get_categories_dict())
@views.route('/pluscart')
@login_required
def plus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        cart_item.quantity = cart_item.quantity + 1
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 3
        }

        return jsonify(data)


@views.route('/minuscart')
@login_required
def minus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        cart_item.quantity = cart_item.quantity - 1
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 3
        }

        return jsonify(data)


@views.route('removecart')
@login_required
def remove_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        db.session.delete(cart_item)
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 3
        }

        return jsonify(data)

@views.route('/place-order')
@login_required
def place_order():
    customer_cart = Cart.query.filter_by(customer_link=current_user.id)
    if customer_cart:
        try:
            total = 0
            for item in customer_cart:
                total += item.product.current_price * item.quantity

            service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)
            create_order_response = service.collect.mpesa_stk_push(phone_number='25470174294 ', email=current_user.email,
                                                                   amount=total + 3, narrative='Purchase of goods')

            for item in customer_cart:
                new_order = Order()
                new_order.quantity = item.quantity
                new_order.price = item.product.current_price
                new_order.status = create_order_response['invoice']['state'].capitalize()
                new_order.payment_id = create_order_response['id']

                new_order.product_link = item.product_link
                new_order.customer_link = item.customer_link

                db.session.add(new_order)

                product = Product.query.get(item.product_link)

                product.in_stock -= item.quantity

                db.session.delete(item)

                db.session.commit()

            flash('Order Placed Successfully')

            return redirect('/orders')
        except Exception as e:
            print(e)
            flash('Order not placed')
            return redirect('/')
    else:
        flash('Your cart is Empty')
        return redirect('/')

@views.route('/orders')
@login_required
def order():
    orders = Order.query.filter_by(customer_link=current_user.id).all()
    return render_template('orders.html', 
                         orders=orders,
                         categories=get_categories_dict())
@views.route('/request-return/<int:order_id>', methods=['GET', 'POST'])
@login_required
def request_return(order_id):
    try:
        # Fetch order or throw 404 if not found
        order = Order.query.get_or_404(order_id)
        
        # Verify order belongs to the current user
        if order.customer_link != current_user.id:
            flash('Unauthorized access', 'error')
            return redirect(url_for('views.order'))
        
        form = CustomerReturnForm()
        
        if form.validate_on_submit():
            # Debugging prints
            print(f"Order ID: {order_id}, Customer ID: {current_user.id}, Product ID: {order.product_link}")
            print(f"Form Data - Quantity: {form.quantity.data}, Reason: {form.reason.data}")
            
            # Create return request
            return_request = Return(
                order_link=order_id,
                customer_link=current_user.id,
                product_link=order.product_link,
                quantity=form.quantity.data,
                reason=form.reason.data,
                status='pending'
            )
            
            db.session.add(return_request)
            db.session.commit()
            
            flash('Return request submitted successfully', 'success')
            return redirect(url_for('views.my_returns'))
        else:
            print(f"Form Errors: {form.errors}")  # Log form validation errors
        
        # Render the return request form
        return render_template('return_request.html', form=form, order=order, categories=get_categories_dict())
        
    except Exception as e:
        flash('Error submitting return request', 'error')
        print(f"Error in request return: {e}")  # Log exception details
        return redirect(url_for('views.order'))


@views.route('/my-returns')
@login_required
def my_returns():
    try:
        returns = Return.query.filter_by(customer_link=current_user.id)\
                      .order_by(Return.return_date.desc())\
                      .all()
                      
        return render_template('my_returns.html', returns=returns, categories=get_categories_dict())
        
    except Exception as e:
        flash('Error loading returns', 'error')
        print(f"Error in my returns: {e}")
        return redirect(url_for('views.home'))

@views.route('/return-details/customer/<int:return_id>')
@login_required
def view_return_details(return_id):
    try:
        return_request = Return.query.get_or_404(return_id)
        
        # Verify return belongs to current user
        if return_request.customer_link != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
            
        return jsonify({
            'success': True,
            'return': {
                'id': return_request.id,
                'order_id': return_request.order_link,
                'product_name': return_request.product.product_name,
                'quantity': return_request.quantity,
                'return_date': return_request.return_date.strftime('%Y-%m-%d %H:%M'),
                'reason': return_request.reason,
                'status': return_request.status,
                'resolution': return_request.resolution,
                'tracking_number': return_request.tracking_number
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    

@views.route('/products/<category>/<subcategory>')
def filtered_products(category, subcategory):
    category_obj = Category.query.filter_by(name=category).first_or_404()
    subcategory_obj = SubCategory.query.filter_by(
        name=subcategory, 
        category_id=category_obj.id
    ).first_or_404()
    
    products = Product.query.filter_by(
        category_id=category_obj.id,
        subcategory_id=subcategory_obj.id
    ).all()
    
    cart_items = {}
    if current_user.is_authenticated:
        cart_items = {
            item.product_link: item 
            for item in Cart.query.filter_by(customer_link=current_user.id).all()
        }
    
    categories_dict = {}
    categories = Category.query.all()
    for cat in categories:
        subcategories = [subcat.name for subcat in cat.subcategories]
        categories_dict[cat.name] = subcategories

    return render_template(
        'filtered_products.html',
        products=products,
        current_category=category,
        current_subcategory=subcategory,
        categories=categories_dict,
        cart_items=cart_items,
        cart=Cart.query.filter_by(customer_link=current_user.id).all() if current_user.is_authenticated else []
    )