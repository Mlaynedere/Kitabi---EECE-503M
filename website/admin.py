from flask import Blueprint, jsonify, render_template, flash, send_from_directory, redirect, request
from flask_login import login_required, current_user
from .forms import ShopItemsForm, OrderForm, InventoryForm
from werkzeug.utils import secure_filename
from .models import Product, Order, Customer, Category, SubCategory, StockHistory
from . import db
from sqlalchemy.orm import joinedload
from datetime import datetime

admin = Blueprint('admin', __name__)

@admin.route('/media/<path:filename>')
def get_image(filename):
    return send_from_directory('../media', filename)
from flask import render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
from . import db
from .models import Product, Category, SubCategory
from .forms import ShopItemsForm

@admin.route('/add-shop-items', methods=['GET', 'POST'])
@login_required
def add_shop_items():
    if current_user.id == 1:
        form = ShopItemsForm()
        categories = Category.query.all()  # Get all categories from DB
        subcategories = SubCategory.query.all()  # Get all subcategories from DB

        # Populate the category and subcategory dropdowns
        form.category.choices = [(category.id, category.name) for category in categories]
        form.subcategory.choices = [(subcategory.id, subcategory.name) for subcategory in subcategories]

        # If the form is submitted, process the data
        if form.validate_on_submit():
            product_name = form.product_name.data
            author = form.author.data
            rating = form.rating.data
            current_price = form.current_price.data
            in_stock = form.in_stock.data
            flash_sale = form.flash_sale.data
            promotion_percentage = form.promotion_percentage.data
            discounted_price = current_price - (current_price * promotion_percentage / 100)

            file = form.product_picture.data

            # Ensure safe file storage
            file_name = secure_filename(file.filename)
            file_path = f'./media/{file_name}'  # Save to the media folder
            file.save(file_path)

            # Get category and subcategory from the form
            category_id = form.category.data
            subcategory_id = form.subcategory.data

            # Create a new product and assign category and subcategory
            new_shop_item = Product(
                product_name=product_name,
                author=author,
                rating=rating,
                current_price=current_price,
                in_stock=in_stock,
                flash_sale=flash_sale,
                promotion_percentage=promotion_percentage,
                discounted_price=discounted_price,
                product_picture=file_path,
                category_id=category_id,  # Linking category to product
                subcategory_id=subcategory_id  # Linking subcategory to product
            )

            try:
                # Add new product to the database
                db.session.add(new_shop_item)
                db.session.commit()
                flash(f'{product_name} added successfully!')
                print('Product Added')
                # Optionally, redirect to another page or refresh
                return redirect(url_for('admin.shop_items'))  # Stay on the same page

            except Exception as e:
                db.session.rollback()  # Rollback in case of error
                print(e)
                flash('An error occurred while adding the product. Please try again.')

        return render_template('add_shop_items.html', form=form, categories=categories, subcategories=subcategories)

    return render_template('404.html')


@admin.route('/shop-items', methods=['GET', 'POST'])
@login_required
def shop_items():
    if current_user.id == 1:
        items = Product.query.order_by(Product.date_added).all()
        low_stock_items = [item for item in items if item.in_stock < 10]  # Low stock threshold
        return render_template('shop_items.html', items=items, low_stock_items=low_stock_items)
    return render_template('404.html')

@admin.route('/update-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def update_item(item_id):
    if current_user.id == 1:
        # Fetch the item to update
        item_to_update = Product.query.get_or_404(item_id)

        # Initialize form
        form = ShopItemsForm()

        # Get categories and subcategories
        categories = Category.query.all()
        subcategories = SubCategory.query.all()

        # Set form choices
        form.category.choices = [(category.id, category.name) for category in categories]
        form.subcategory.choices = [(subcategory.id, subcategory.name) for subcategory in subcategories]

        if request.method == 'GET':
            # Pre-populate form with existing data
            form.product_name.data = item_to_update.product_name
            form.author.data = item_to_update.author
            form.rating.data = item_to_update.rating
            form.current_price.data = item_to_update.current_price
            form.in_stock.data = item_to_update.in_stock
            form.flash_sale.data = item_to_update.flash_sale
            form.promotion_percentage.data = item_to_update.promotion_percentage
            form.category.data = item_to_update.category_id
            form.subcategory.data = item_to_update.subcategory_id

        if form.validate_on_submit():
            try:
                # Update the item fields
                item_to_update.product_name = form.product_name.data
                item_to_update.author = form.author.data
                item_to_update.rating = form.rating.data
                item_to_update.current_price = form.current_price.data
                item_to_update.in_stock = form.in_stock.data
                item_to_update.flash_sale = form.flash_sale.data
                item_to_update.promotion_percentage = form.promotion_percentage.data
                item_to_update.discounted_price = (
                    form.current_price.data - 
                    (form.current_price.data * form.promotion_percentage.data / 100)
                )
                
                # Important: Update category and subcategory
                item_to_update.category_id = form.category.data
                item_to_update.subcategory_id = form.subcategory.data

                # Handle image upload if new image is provided
                if form.product_picture.data:
                    file = form.product_picture.data
                    file_name = secure_filename(file.filename)
                    file_path = f'./media/{file_name}'
                    file.save(file_path)
                    item_to_update.product_picture = file_path

                # Commit all changes
                db.session.commit()
                flash(f'{item_to_update.product_name} updated successfully!', 'success')
                return redirect('/shop-items')

            except Exception as e:
                db.session.rollback()
                print('Update error:', str(e))
                flash('An error occurred while updating the item. Please try again.', 'error')

        # For both GET and failed POST
        return render_template(
            'update_item.html',
            form=form,
            current_image=item_to_update.product_picture,
            categories=categories,
            subcategories=subcategories
        )

    return render_template('404.html')

@admin.route('/delete-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def delete_item(item_id):
    if current_user.id == 1:
        try:
            item_to_delete = Product.query.get(item_id)
            db.session.delete(item_to_delete)
            db.session.commit()
            flash('One Item deleted')
            return redirect('/shop-items')
        except Exception as e:
            print('Item not deleted', e)
            flash('Item not deleted!!')
        return redirect('/shop-items')

    return render_template('404.html')

@admin.route('/view-orders')
@login_required
def order_view():
    if current_user.id == 1:
        orders = Order.query.all()
        return render_template('view_orders.html', orders=orders)
    return render_template('404.html')

@admin.route('/update-order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def update_order(order_id):
    if current_user.id == 1:
        form = OrderForm()

        order = Order.query.get(order_id)

        if form.validate_on_submit():
            status = form.order_status.data
            order.status = status

            try:
                db.session.commit()
                flash(f'Order {order_id} Updated successfully')
                return redirect('/view-orders')
            except Exception as e:
                print(e)
                flash(f'Order {order_id} not updated')
                return redirect('/view-orders')

        return render_template('order_update.html', form=form)

    return render_template('404.html')


@admin.route('/customers')
@login_required
def display_customers():
    if current_user.id == 1:
        customers = Customer.query.all()
        return render_template('customers.html', customers=customers)
    return render_template('404.html')

@admin.route('/admin-page')
@login_required
def admin_page():
    if current_user.id == 1:
        return render_template('admin.html')
    return render_template('404.html')
@admin.route('/inventory-management')
@login_required
def inventory_management():
    if current_user.id == 1:
        # Get all products with their current stock levels
        products = Product.query.all()
        
        # Get products with low stock
        low_stock_products = Product.query.filter(
            Product.in_stock <= Product.low_stock_threshold
        ).all()
        
        # Group products by warehouse
        warehouse_inventory = {}
        for product in products:
            if product.warehouse_location not in warehouse_inventory:
                warehouse_inventory[product.warehouse_location] = []
            warehouse_inventory[product.warehouse_location].append(product)

        return render_template(
            'inventory_management.html',
            products=products,
            low_stock_products=low_stock_products,
            warehouse_inventory=warehouse_inventory
        )
    return render_template('404.html')

@admin.route('/inventory-report')
@login_required
def inventory_report():
    if current_user.id == 1:
        # Basic stats
        total_products = Product.query.count()
        low_stock_items = Product.query.filter(
            Product.in_stock <= Product.low_stock_threshold
        ).all()
        low_stock_products = len(low_stock_items)

        # Most popular products
        most_popular_products = Product.query.order_by(
            Product.rating.desc()
        ).limit(10).all()

        # Calculate total stock value and category statistics
        category_stock = {}
        total_stock_value = 0
        
        # Get all products with their categories
        products = Product.query.join(Category).all()
        
        for product in products:
            # Calculate product value
            product_value = product.discounted_price * product.in_stock
            total_stock_value += product_value
            
            # Aggregate category statistics
            if product.category.name not in category_stock:
                category_stock[product.category.name] = {
                    'total_items': 0,
                    'value': 0
                }
            category_stock[product.category.name]['total_items'] += product.in_stock
            category_stock[product.category.name]['value'] += product_value

        # Warehouse statistics
        warehouse_stats = {}
        warehouses = db.session.query(
            Product.warehouse_location
        ).distinct().all()
        
        for warehouse in warehouses:
            warehouse_name = warehouse[0]
            warehouse_products = Product.query.filter_by(
                warehouse_location=warehouse_name
            ).all()
            
            warehouse_stats[warehouse_name] = {
                'total_products': len(warehouse_products),
                'low_stock_items': len([
                    p for p in warehouse_products 
                    if p.in_stock <= p.low_stock_threshold
                ]),
                'total_value': sum(
                    p.discounted_price * p.in_stock 
                    for p in warehouse_products
                )
            }

        return render_template(
            'inventory_report.html',
            total_products=total_products,
            low_stock_products=low_stock_products,
            low_stock_items=low_stock_items,
            most_popular_products=most_popular_products,
            total_stock_value=total_stock_value,
            category_stock=category_stock,
            warehouse_stats=warehouse_stats
        )
    return render_template('404.html')

@admin.route('/update-inventory/<int:product_id>', methods=['GET', 'POST'])
@login_required
def update_inventory(product_id):
    if current_user.id == 1:
        product = Product.query.get_or_404(product_id)
        form = InventoryForm()
        
        if request.method == 'GET':
            form.warehouse_location.data = product.warehouse_location
            form.low_stock_threshold.data = product.low_stock_threshold
            form.in_stock.data = product.in_stock
        
        if form.validate_on_submit():
            # Record the stock change in history
            previous_stock = product.in_stock
            new_stock = form.in_stock.data
            stock_change = new_stock - previous_stock
            
            stock_history = StockHistory(
                product_id=product.id,
                previous_stock=previous_stock,
                new_stock=new_stock,
                change=stock_change,
                warehouse_location=form.warehouse_location.data,
                updated_by=current_user.id
            )
            
            # Update product
            product.warehouse_location = form.warehouse_location.data
            product.low_stock_threshold = form.low_stock_threshold.data
            product.in_stock = new_stock
            product.last_stock_update = datetime.utcnow()
            
            try:
                db.session.add(stock_history)
                db.session.commit()
                flash(f'Inventory updated for {product.product_name}', 'success')
                return redirect(url_for('admin.inventory_management'))
            except Exception as e:
                db.session.rollback()
                flash('Error updating inventory', 'error')
                
        # Get stock history for this product
        history = StockHistory.query.filter_by(
            product_id=product_id
        ).order_by(StockHistory.date_updated.desc()).all()
                
        return render_template(
            'update_inventory.html',
            form=form,
            product=product,
            history=history
        )
    return render_template('404.html')

@admin.route('/get-subcategories/<int:category_id>')
@login_required
def get_subcategories(category_id):
    subcategories = SubCategory.query.filter_by(category_id=category_id).all()
    return jsonify({'subcategories': [{'id': subcategory.id, 'name': subcategory.name} for subcategory in subcategories]})
