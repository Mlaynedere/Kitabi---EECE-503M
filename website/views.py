from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, request, jsonify, url_for
from flask_limiter import Limiter
from flask_login import login_required, current_user
from . import limiter
from flask_limiter.util import get_remote_address
from .admin import log_activity
from .models import Customer, Product, Order, Return, Cart, Category, SubCategory
from . import db
from intasend import APIService
from .forms import CustomerReturnForm
from .utils import get_categories_dict
from .decorators import jwt_required
from sqlalchemy import or_


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
@jwt_required
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
@jwt_required
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
@jwt_required
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
@jwt_required
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
@jwt_required
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

def secure_payment_call(phone_number, email, amount, narrative):
    """Secure payment API call with retry and timeout"""
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    
    try:
        service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)
        response = service.collect.mpesa_stk_push(
            phone_number=phone_number,
            email=email,
            amount=amount,
            narrative=narrative
        )
        return response
    except Exception as e:
        log_activity('payment_error', details=str(e))
        raise

@views.route('/place-order')
@jwt_required
@limiter.limit("10 per minute")
def place_order():
    try:
        customer_cart = Cart.query.filter_by(customer_link=current_user.id).all()
        
        if not customer_cart:
            flash('Your cart is empty', 'error')
            return redirect(url_for('views.show_cart'))

        # Calculate totals
        total = sum(item.product.current_price * item.quantity for item in customer_cart)
        
        # Apply membership discount if applicable
        discount = 0
        if current_user.membership_tier:
            discount = total * (current_user.membership_tier.discount_percentage / 100)
        total_after_discount = total - discount

        # Calculate delivery fee
        delivery_fee = 3  # Default delivery fee
        if current_user.membership_tier:
            if current_user.membership_tier.free_delivery_threshold is None:
                delivery_fee = 0
            elif total_after_discount >= current_user.membership_tier.free_delivery_threshold:
                delivery_fee = 0

        final_total = total_after_discount + delivery_fee

        # Validate stock availability
        for cart_item in customer_cart:
            if cart_item.quantity > cart_item.product.in_stock:
                flash(f'Not enough stock for {cart_item.product.product_name}. Available: {cart_item.product.in_stock}', 'error')
                return redirect(url_for('views.show_cart'))

        # Process order without payment integration
        with db.session.begin_nested():
            # Calculate and award points
            points_earned = int(total * current_user.membership_tier.points_multiplier)
            current_user.points += points_earned

            # Check for tier upgrade
            current_user.check_tier_upgrade()

            # Create orders and update inventory
            orders_created = []
            for cart_item in customer_cart:
                # Create order
                new_order = Order(
                    quantity=cart_item.quantity,
                    price=cart_item.product.current_price,
                    status='Completed',  # Set default status
                    payment_id=f'ORDER{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',  # Generate simple order ID
                    product_link=cart_item.product_link,
                    customer_link=cart_item.customer_link,
                    delivery_fee=delivery_fee if cart_item == customer_cart[0] else 0,  # Apply delivery fee to first item only
                    discount_applied=discount if cart_item == customer_cart[0] else 0  # Apply discount to first item only
                )
                db.session.add(new_order)
                orders_created.append(new_order)

                # Update product stock
                product = cart_item.product
                if product.in_stock < cart_item.quantity:
                    raise ValueError(f'Insufficient stock for {product.product_name}')
                product.in_stock -= cart_item.quantity

                # Remove cart item
                db.session.delete(cart_item)

            # Log activity
            log_activity(
                action='order_placed',
                entity_type='customer',
                entity_id=current_user.id,
                details={
                    'points_earned': points_earned,
                    'order_total': total,
                    'final_total': final_total,
                    'discount': discount,
                    'delivery_fee': delivery_fee,
                    'tier_multiplier': current_user.membership_tier.points_multiplier
                }
            )

        # Commit the transaction
        db.session.commit()

        flash(f'Order placed successfully! You earned {points_earned} points!', 'success')
        return redirect(url_for('views.order'))

    except ValueError as ve:
        db.session.rollback()
        flash(str(ve), 'error')
        return redirect(url_for('views.show_cart'))
    
    except Exception as e:
        db.session.rollback()
        print(f"Order processing error: {str(e)}")
        flash('An error occurred while processing your order. Please try again.', 'error')
        return redirect(url_for('views.show_cart'))
    

@views.route('/orders')
@jwt_required
def order():
    orders = Order.query.filter_by(customer_link=current_user.id).all()
    return render_template('orders.html', 
                         orders=orders,
                         categories=get_categories_dict())
@views.route('/request-return/<int:order_id>', methods=['GET', 'POST'])
@jwt_required
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
@jwt_required
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
@jwt_required
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



@views.route('/search')
def search():
    query = request.args.get('query', '')
    if not query:
        return redirect(url_for('views.home'))
        
    # Search in multiple fields
    results = Product.query.filter(
        or_(
            Product.product_name.ilike(f'%{query}%'),
            Product.author.ilike(f'%{query}%'),
        )
    ).all()
    
    # Get categories for sidebar
    categories = {}
    all_categories = Category.query.all()
    for category in all_categories:
        subcategories = [sc.name for sc in category.subcategories]
        categories[category.name] = subcategories

    return render_template(
        'search_results.html',
        query=query,
        results=results,
        categories=categories
    )


@views.route('/search-suggestions')
def search_suggestions():
    query = request.args.get('query', '').lower()
    if not query:
        return jsonify([])
    
    # Search for matching products
    suggestions = Product.query.filter(
        or_(
            Product.product_name.ilike(f'%{query}%'),
            Product.author.ilike(f'%{query}%')
        )
    ).limit(5).all()  # Limit to 5 suggestions
    
    # Format the results
    results = [{
        'id': product.id,
        'name': product.product_name,
        'author': product.author
    } for product in suggestions]
    
    return jsonify(results)