from flask import Blueprint, Response, jsonify, render_template, flash, send_from_directory, redirect, request, url_for
from flask_limiter import Limiter
from flask_login import login_required, current_user
from flask_limiter.util import get_remote_address
from website.security import safe_query
from .decorators import admin_required, check_permission, jwt_required
from .forms import ShopItemsForm, OrderForm, InventoryForm, RoleForm, AssignRoleForm, ProcessReturnForm, MembershipTierForm, AwardPointsForm, BulkUploadForm
from werkzeug.utils import secure_filename
from .models import Product, Order, Customer, Category, SubCategory, StockHistory, ActivityLog, Role, Return, MembershipTier
from . import db, limiter
from sqlalchemy.orm import joinedload
from datetime import datetime
import os
import json
import pandas as pd

admin = Blueprint('admin', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_activity(action, entity_type=None, entity_id=None, details=None):
    try:
        log = ActivityLog(
            user_id=current_user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")
        db.session.rollback()

@admin.route('/media/<path:filename>')
def get_image(filename):
    return send_from_directory('../media', filename)

@admin.route('/add-shop-items', methods=['GET', 'POST'])
@login_required
@admin_required
@check_permission('manage_products')
@limiter.limit("50 per hour")
def add_shop_items():
    form = ShopItemsForm()
    
    try:
        # Get all categories and subcategories
        categories = Category.query.all()
        subcategories = SubCategory.query.all()

        # Populate form choices
        form.category.choices = [(category.id, category.name) for category in categories]
        form.subcategory.choices = [(subcategory.id, subcategory.name) for subcategory in subcategories]

        if form.validate_on_submit():
            try:
                # Extract form data
                product_name = form.product_name.data
                author = form.author.data
                rating = form.rating.data
                current_price = form.current_price.data
                in_stock = form.in_stock.data
                flash_sale = form.flash_sale.data
                promotion_percentage = form.promotion_percentage.data
                category_id = form.category.data
                subcategory_id = form.subcategory.data

                # Calculate discounted price
                discounted_price = current_price - (current_price * promotion_percentage / 100)

                # Handle file upload
                file = form.product_picture.data
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join('./media', filename)
                    
                    # Ensure media directory exists
                    os.makedirs('./media', exist_ok=True)
                    
                    # Save the file
                    file.save(file_path)
                else:
                    flash('Invalid file type or no file provided', 'error')
                    return render_template('add_shop_items.html', form=form, 
                                        categories=categories, 
                                        subcategories=subcategories)

                # Create new product instance
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
                    category_id=category_id,
                    subcategory_id=subcategory_id,
                    warehouse_location='Main Warehouse',  # Default value
                    low_stock_threshold=10  # Default value
                )

                # Add to database
                db.session.add(new_shop_item)
                db.session.commit()

                # Log the activity
                log_activity(
                    action='create_product',
                    entity_type='product',
                    entity_id=new_shop_item.id,
                    details={
                        'product_name': product_name,
                        'author': author,
                        'price': current_price,
                        'stock': in_stock,
                        'category_id': category_id,
                        'subcategory_id': subcategory_id,
                        'promotion': promotion_percentage if promotion_percentage else 0
                    }
                )

                flash(f'{product_name} added successfully!', 'success')
                return redirect(url_for('admin.shop_items'))

            except Exception as e:
                db.session.rollback()
                print(f"Error adding product: {e}")
                flash('An error occurred while adding the product. Please try again.', 'error')
                
        elif request.method == 'POST':
            log_activity(
                action='failed_product_creation',
                entity_type='product',
                details={'form_errors': form.errors}
            )
            
        return render_template('add_shop_items.html', 
                             form=form, 
                             categories=categories, 
                             subcategories=subcategories)

    except Exception as e:
        print(f"Error in add_shop_items: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('admin.admin_page'))



@admin.route('/shop-items', methods=['GET', 'POST'])
@login_required
@admin_required
@check_permission('manage_products')
def shop_items():
    items = Product.query.order_by(Product.date_added).all()
    low_stock_items = [item for item in items if item.in_stock < 10]
    return render_template('shop_items.html', items=items, low_stock_items=low_stock_items)


@admin.route('/update-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
@admin_required
@check_permission('manage_products')
@limiter.limit("50 per hour") 
def update_item(item_id):
    try:
        item_to_update = Product.query.get_or_404(item_id)
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
                # Store original values for logging
                original_values = {
                    'product_name': item_to_update.product_name,
                    'price': item_to_update.current_price,
                    'stock': item_to_update.in_stock,
                    'category': item_to_update.category_id,
                    'subcategory': item_to_update.subcategory_id
                }

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
                
                item_to_update.category_id = form.category.data
                item_to_update.subcategory_id = form.subcategory.data

                # Handle image upload if new image is provided
                if form.product_picture.data:
                    file = form.product_picture.data
                    if allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join('./media', filename)
                        
                        # Ensure media directory exists
                        os.makedirs('./media', exist_ok=True)
                        
                        file.save(file_path)
                        item_to_update.product_picture = file_path
                    else:
                        flash('Invalid file type. Please upload an image file.', 'error')
                        raise ValueError('Invalid file type')

                # Commit all changes
                db.session.commit()

                # Log the update activity
                log_activity(
                    action='update_product',
                    entity_type='product',
                    entity_id=item_id,
                    details={
                        'original_values': original_values,
                        'updated_values': {
                            'product_name': form.product_name.data,
                            'price': form.current_price.data,
                            'stock': form.in_stock.data,
                            'category': form.category.data,
                            'subcategory': form.subcategory.data
                        }
                    }
                )

                flash(f'{item_to_update.product_name} updated successfully!', 'success')
                return redirect(url_for('admin.shop_items'))

            except ValueError as ve:
                # File type error already handled
                pass
            except Exception as e:
                db.session.rollback()
                print(f'Update error: {str(e)}')
                flash('An error occurred while updating the item. Please try again.', 'error')
                log_activity(
                    action='failed_product_update',
                    entity_type='product',
                    entity_id=item_id,
                    details={'error': str(e)}
                )

        elif request.method == 'POST':
            # Log form validation errors
            log_activity(
                action='failed_product_update',
                entity_type='product',
                entity_id=item_id,
                details={'form_errors': form.errors}
            )

        # For both GET and failed POST
        return render_template(
            'update_item.html',
            form=form,
            current_image=item_to_update.product_picture,
            categories=categories,
            subcategories=subcategories,
            item=item_to_update  # Added to help with form UI
        )

    except Exception as e:
        flash('Error accessing product information', 'error')
        print(f"Error in update_item: {e}")
        return render_template('404.html')

@admin.route('/delete-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
@admin_required
@check_permission('manage_products')
@limiter.limit("20 per hour")
def delete_item(item_id):
    try:
        item_to_delete = Product.query.get(item_id)
        db.session.delete(item_to_delete)
        db.session.commit()
        
        log_activity(
            action='delete_product',
            entity_type='product',
            entity_id=item_id,
            details={'product_name': item_to_delete.product_name}
        )
        
        flash('Product deleted successfully', 'success')
        return redirect(url_for('admin.shop_items'))
    except Exception as e:
        print('Item not deleted', e)
        flash('Error deleting product', 'error')
        return redirect(url_for('admin.shop_items'))


@admin.route('/view-orders')
@login_required
@admin_required
@check_permission('manage_orders')
def order_view():
    orders = Order.query.all()
    return render_template('view_orders.html', orders=orders)


@admin.route('/update-order/<int:order_id>', methods=['GET', 'POST'])
@login_required
@admin_required
@check_permission('manage_orders')
@limiter.limit("30 per hour")
def update_order(order_id):
    form = OrderForm()
    order = Order.query.get_or_404(order_id)

    if form.validate_on_submit():
        try:
            previous_status = order.status
            order.status = form.order_status.data
            db.session.commit()
            
            log_activity(
                action='update_order',
                entity_type='order',
                entity_id=order_id,
                details={
                    'previous_status': previous_status,
                    'new_status': order.status
                }
            )
            
            flash(f'Order {order_id} updated successfully', 'success')
            return redirect(url_for('admin.order_view'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating order: {str(e)}', 'error')
            return redirect(url_for('admin.order_view'))

    return render_template('order_update.html', form=form, order=order)


@admin.route('/customers')
@login_required
@admin_required
@check_permission('manage_users')
def display_customers():
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)

@admin.route('/admin-page')
@admin_required
def admin_page():
    try:
        # Get statistics
        total_orders = Order.query.count()
        total_revenue = db.session.query(
            db.func.sum(Order.price * Order.quantity)
        ).scalar() or 0
        low_stock_count = Product.query.filter(
            Product.in_stock <= Product.low_stock_threshold
        ).count()
        active_users = Customer.query.filter_by(status='active').count()
        
        # Get recent activities
        recent_activities = ActivityLog.query.order_by(
            ActivityLog.timestamp.desc()
        ).limit(5).all()
        pending_returns = Return.query.filter_by(status='pending').count()

        return render_template(
            'admin.html',
            total_orders=total_orders,
            total_revenue="{:,.2f}".format(total_revenue),
            low_stock_count=low_stock_count,
            active_users=active_users,
            pending_returns=pending_returns,
            recent_activities=recent_activities
        )
    except Exception as e:
        flash('Error loading dashboard statistics', 'error')
        print(f"Error in admin dashboard: {e}")
        return render_template('admin.html')
    
@admin.route('/inventory-management')
@login_required
@admin_required
@check_permission('manage_inventory')
def inventory_management():
    try:
        # Get all products with their current stock levels
        products = Product.query.options(
            joinedload(Product.category)
        ).all()
        print(f"Found {len(products)} products")  # Debug print

        # Get products with low stock
        low_stock_products = Product.query.filter(
            Product.in_stock <= Product.low_stock_threshold
        ).options(
            joinedload(Product.category)
        ).all()
        print(f"Found {len(low_stock_products)} low stock products")  # Debug print
        
        # Group products by warehouse
        warehouse_inventory = {}
        for product in products:
            warehouse_location = product.warehouse_location or 'Main Warehouse'
            if warehouse_location not in warehouse_inventory:
                warehouse_inventory[warehouse_location] = []
            warehouse_inventory[warehouse_location].append(product)
        
        print(f"Warehouse inventory: {warehouse_inventory.keys()}")  # Debug print
        for warehouse, items in warehouse_inventory.items():
            print(f"Warehouse {warehouse}: {len(items)} items")  # Debug print

        # Let's also check if products have all required attributes
        for product in products[:1]:  # Check first product as example
            print(f"""
            Product debug info:
            - Name: {product.product_name}
            - Stock: {product.in_stock}
            - Threshold: {product.low_stock_threshold}
            - Warehouse: {product.warehouse_location}
            - Category: {product.category.name if product.category else 'No category'}
            - Last Update: {product.last_stock_update}
            """)

        return render_template(
            'inventory_management.html',
            products=products,
            low_stock_products=low_stock_products,
            warehouse_inventory=warehouse_inventory
        )
    except Exception as e:
        print(f"Error in inventory management: {str(e)}")  # Debug print
        flash('Error loading inventory management page', 'error')
        return redirect(url_for('admin.admin_page'))
    
@admin.route('/inventory-report')
@login_required
@admin_required
@check_permission('view_reports')
def inventory_report():
    try:
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

        # Log the activity
        log_activity(
            action='view_inventory_report',
            entity_type='report',
            details={
                'total_products': total_products,
                'low_stock_products': low_stock_products
            }
        )

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
    except Exception as e:
        flash('Error generating inventory report', 'error')
        print(f"Error in inventory report: {e}")
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


from sqlalchemy import text

@admin.route('/get-subcategories/<int:category_id>')
@login_required
@limiter.limit("30 per minute", key_func=get_remote_address)
def get_subcategories(category_id):
    try:
        # Validate input
        if not isinstance(category_id, int) or category_id < 1:
            return jsonify({'error': 'Invalid category ID'}), 400
        
        # Use safe query with explicit text() declaration
        query = text("SELECT id, name FROM sub_category WHERE category_id = :cat_id ORDER BY name")
        subcategories = safe_query(
            query,
            {'cat_id': category_id}
        ).fetchall()
        
        # Convert rows to dictionaries
        subcategories_list = [
            {'id': row[0], 'name': row[1]} 
            for row in subcategories
        ]
        
        # Log the response for debugging
        print(f"Found {len(subcategories_list)} subcategories for category {category_id}")
        
        return jsonify({
            'subcategories': subcategories_list
        })
    except Exception as e:
        log_activity('api_error', details=str(e))
        print(f"Error in get_subcategories: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    
@admin.route('/roles', methods=['GET'])
@login_required
@admin_required
@check_permission('manage_users')
def manage_roles():
    try:
        roles = Role.query.all()
        roles_data = []
        
        for role in roles:
            # Ensure permissions is a proper list
            if isinstance(role.permissions, str):
                try:
                    permissions = json.loads(role.permissions)
                except:
                    permissions = []
            else:
                permissions = role.permissions or []
                
            role_data = {
                'id': role.id,
                'name': role.name,
                'description': role.description or '',
                'permissions': [p.strip() for p in permissions if p], # Clean up permissions
                'user_count': role.users.count()
            }
            roles_data.append(role_data)
            
        return render_template('admin_roles.html', roles=roles_data)
        
    except Exception as e:
        print(f"Error in manage_roles: {str(e)}")
        flash('Error loading roles', 'error')
        return redirect(url_for('admin.admin_page'))
@admin.route('/roles/add', methods=['GET', 'POST'])
@login_required
@admin_required
@check_permission('manage_users')
def add_role():
    form = RoleForm()
    
    if form.validate_on_submit():
        try:
            # Create new role
            role = Role(
                name=form.name.data,
                description=form.description.data,
                permissions=form.permissions.data  # Will be a list of selected permissions
            )
            
            db.session.add(role)
            db.session.commit()
            
            # Log the activity
            log_activity(
                action='create_role',
                entity_type='role',
                entity_id=role.id,
                details={
                    'role_name': role.name,
                    'permissions': role.permissions
                }
            )
            
            flash('Role created successfully', 'success')
            return redirect(url_for('admin.manage_roles'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating role: {str(e)}")
            flash('Error creating role', 'error')
    
    return render_template('add_role.html', form=form)

@admin.route('/users/<int:user_id>/roles', methods=['GET', 'POST'])
@login_required
@admin_required
@check_permission('manage_users')
def assign_roles(user_id):
    user = Customer.query.get_or_404(user_id)
    form = AssignRoleForm()
    form.roles.choices = [(r.id, r.name) for r in Role.query.all()]
    
    if form.validate_on_submit():
        try:
            previous_roles = [role.name for role in user.roles]
            user.roles = Role.query.filter(Role.id.in_(form.roles.data)).all()
            db.session.commit()
            
            log_activity(
                action='assign_roles',
                entity_type='user',
                entity_id=user.id,
                details={
                    'previous_roles': previous_roles,
                    'new_roles': [role.name for role in user.roles]
                }
            )
            
            flash('Roles assigned successfully', 'success')
            return redirect(url_for('admin.display_customers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error assigning roles: {str(e)}', 'error')
    
    form.roles.data = [role.id for role in user.roles]
    return render_template('assign_roles.html', form=form, user=user)

@admin.route('/activity-logs')
@login_required
@admin_required
@check_permission('view_reports')
def view_activity_logs():
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    return render_template('activity_logs.html', logs=logs)

@admin.route('/returns-management')
@login_required
@admin_required
@check_permission('manage_returns')
def returns_management():
    try:
        returns = Return.query.options(
            joinedload(Return.customer),
            joinedload(Return.product),
            joinedload(Return.order)
        ).order_by(Return.return_date.desc()).all()
        
        return render_template('admin_returns.html', returns=returns)
    except Exception as e:
        flash('Error loading returns', 'error')
        print(f"Error in returns management: {e}")
        return redirect(url_for('admin.admin_page'))

@admin.route('/process-return/<int:return_id>', methods=['GET', 'POST'])
@login_required
@admin_required
@check_permission('manage_returns')
def process_return(return_id):
    try:
        return_request = Return.query.get_or_404(return_id)
        order = return_request.order
        form = ProcessReturnForm()
        quantity_returned = Return.query.filter_by(order_link=order.id).filter(Return.id != return_id).with_entities(db.func.sum(Return.quantity)).scalar() or 0
        
        # Calculate the remaining quantity that can be returned
        remaining_quantity = order.quantity - quantity_returned

        # Calculate the max refund based on the remaining quantity
        max_refund_amount = remaining_quantity * order.price

        if form.validate_on_submit():
            original_status = return_request.status
            
            return_request.status = form.status.data
            return_request.resolution = form.resolution.data
            return_request.admin_notes = form.admin_notes.data
            return_request.processed_by = current_user.id
            return_request.processed_date = datetime.utcnow()

            if form.resolution.data == 'refund':
                return_request.refund_amount = form.refund_amount.data
            
            if form.tracking_number.data:
                return_request.tracking_number = form.tracking_number.data

            if form.status.data == 'approved' and form.resolution.data == 'replacement':
                # Create new order for replacement
                replacement_order = Order(
                    customer_link=return_request.customer_link,
                    product_link=return_request.product_link,
                    quantity=return_request.quantity,
                    price=0,  # Free replacement
                    status='Processing',
                    payment_id='replacement'
                )
                db.session.add(replacement_order)
                return_request.replacement_order_id = replacement_order.id

            db.session.commit()

            # Log the activity
            log_activity(
                action='process_return',
                entity_type='return',
                entity_id=return_id,
                details={
                    'previous_status': original_status,
                    'new_status': return_request.status,
                    'resolution': return_request.resolution
                }
            )

            flash('Return request processed successfully', 'success')
            return redirect(url_for('admin.returns_management'))

        # For GET request, pre-populate form
        if request.method == 'GET':
            form.status.data = return_request.status
            form.resolution.data = return_request.resolution
            form.admin_notes.data = return_request.admin_notes
            form.refund_amount.data = return_request.refund_amount
            form.tracking_number.data = return_request.tracking_number

        return render_template('process_return.html', 
                            form=form, 
                            return_request=return_request,
                            max_refund_amount=max_refund_amount)

    except Exception as e:
        flash('Error processing return request', 'error')
        print(f"Error in process return: {e}")
        return redirect(url_for('admin.returns_management'))

@admin.route('/return-details/admin/<int:return_id>')
@login_required
@admin_required
@check_permission('manage_returns')
def return_details(return_id):
    try:
        return_request = Return.query.get_or_404(return_id)
        return jsonify({
            'success': True,
            'return': {
                'id': return_request.id,
                'customer_name': return_request.customer.full_name,
                'customer_email': return_request.customer.email,
                'product_name': return_request.product.product_name,
                'order_id': return_request.order_link,
                'return_date': return_request.return_date.strftime('%Y-%m-%d %H:%M'),
                'status': return_request.status,
                'reason': return_request.reason,
                'resolution': return_request.resolution,
                'refund_amount': return_request.refund_amount,
                'tracking_number': return_request.tracking_number
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    

@admin.route('/membership-tiers', methods=['GET'])
@login_required
@admin_required
@check_permission('manage_users')
def membership_tiers():
    tiers = MembershipTier.query.all()
    return render_template('membership_tiers.html', tiers=tiers)

@admin.route('/membership-tiers/add', methods=['GET', 'POST'])
@login_required
@admin_required
@check_permission('manage_users')
@limiter.limit("10 per hour")
def add_membership_tier():
    try:
        print("Accessing add membership tier route")  # Debug print
        form = MembershipTierForm()
        
        if form.validate_on_submit():
            try:
                tier = MembershipTier(
                    name=form.name.data,
                    discount_percentage=form.discount_percentage.data,
                    free_delivery_threshold=form.free_delivery_threshold.data,
                    early_access=form.early_access.data,
                    priority_support=form.priority_support.data,
                    points_multiplier=form.points_multiplier.data
                )
                db.session.add(tier)
                db.session.commit()
                
                log_activity(
                    action='create_membership_tier',
                    entity_type='membership_tier',
                    entity_id=tier.id,
                    details={'tier_name': tier.name}
                )
                
                flash('Membership tier created successfully', 'success')
                return redirect(url_for('admin.membership_tiers'))
                
            except Exception as e:
                db.session.rollback()
                print(f"Error creating tier: {e}")
                flash('Error creating membership tier', 'error')
        
        elif request.method == 'POST':
            print(f"Form validation errors: {form.errors}")  # Debug print
            
        return render_template('add_membership_tier.html', form=form)
        
    except Exception as e:
        print(f"Route error: {e}")  # Debug print
        flash('An error occurred', 'error')
        return redirect(url_for('membership_tiers'))
    
@admin.route('/membership-tiers/edit/<int:tier_id>', methods=['GET', 'POST'])
@login_required
@admin_required
@check_permission('manage_users')
@limiter.limit("20 per hour")
def edit_membership_tier(tier_id):
    tier = MembershipTier.query.get_or_404(tier_id)
    form = MembershipTierForm(obj=tier)
    
    if form.validate_on_submit():
        tier.name = form.name.data
        tier.discount_percentage = form.discount_percentage.data
        tier.free_delivery_threshold = form.free_delivery_threshold.data
        tier.early_access = form.early_access.data
        tier.priority_support = form.priority_support.data
        tier.points_multiplier = form.points_multiplier.data
        
        try:
            db.session.commit()
            log_activity(
                action='update_membership_tier',
                entity_type='membership_tier',
                entity_id=tier.id,
                details={'tier_name': tier.name}
            )
            flash('Membership tier updated successfully', 'success')
            return redirect(url_for('membership_tiers'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating membership tier', 'error')
            print(f"Error updating tier: {e}")
    
    return render_template('edit_membership_tier.html', form=form, tier=tier)
@admin.route('/customers/points', methods=['GET'])
@login_required
@admin_required
@check_permission('manage_users')
@limiter.limit("50 per hour")
def manage_customer_points():
    # Get all customers with their points and tiers
    customers = Customer.query.order_by(Customer.points.desc()).all()
    return render_template('customer_points_list.html', customers=customers)

@admin.route('/customers/points/<int:customer_id>', methods=['GET', 'POST'])
@login_required
@admin_required
@check_permission('manage_users')
def manage_customer_points_detail(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    form = AwardPointsForm()
    
    if form.validate_on_submit():
        previous_points = customer.points
        customer.points += form.points.data
        customer.check_tier_upgrade()
        
        try:
            db.session.commit()
            log_activity(
                action='award_points',
                entity_type='customer',
                entity_id=customer.id,
                details={
                    'points_awarded': form.points.data,
                    'reason': form.reason.data,
                    'previous_points': previous_points,
                    'new_points': customer.points,
                    'previous_tier': customer.membership_tier.name
                }
            )
            flash(f'Successfully awarded {form.points.data} points to {customer.username}', 'success')
            return redirect(url_for('manage_customer_points'))
        except Exception as e:
            db.session.rollback()
            flash('Error awarding points', 'error')
            print(f"Error awarding points: {e}")
    
    return render_template('manage_points.html', form=form, customer=customer)


import os
import requests
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from flask import Blueprint, request, flash, redirect, url_for, render_template
from io import StringIO
import csv

def validate_csv_headers(headers):
    """Validate that all required headers are present in the CSV file."""
    required_headers = {
        'product_name', 'author', 'rating', 'current_price', 
        'in_stock', 'category_id', 'subcategory_id', 
        'promotion_percentage', 'flash_sale', 'product_picture'
    }
    return required_headers.issubset(set(headers))

from urllib.parse import urlparse
from werkzeug.utils import secure_filename

def download_image(image_url, media_path):
    """Download image from URL with fallback to placeholder."""
    try:
        # Check if image_url is empty or None
        if not image_url:
            return get_placeholder_image_path()
            
        # Parse URL to get filename
        filename = secure_filename(os.path.basename(urlparse(image_url).path))
        if not filename:
            filename = f"product_{os.urandom(8).hex()}.jpg"
        
        # Ensure file has an extension
        if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
            filename += '.jpg'
            
        file_path = os.path.join(media_path, filename)
        
        # Try to download image
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            return os.path.join('./media', filename)
            
        except requests.exceptions.RequestException:
            # If download fails, use placeholder
            return get_placeholder_image_path()
            
    except Exception as e:
        print(f"Error handling image {image_url}: {str(e)}")
        return get_placeholder_image_path()

def get_placeholder_image_path():
    """Return path to placeholder image."""
    placeholder_path = os.path.join('./media', 'placeholder.jpg')
    
    # Create placeholder if it doesn't exist
    if not os.path.exists(placeholder_path):
        create_placeholder_image(placeholder_path)
        
    return './media/placeholder.jpg'

def create_placeholder_image(path):
    """Create a simple placeholder image."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a 300x300 white image
        img = Image.new('RGB', (300, 300), color='white')
        d = ImageDraw.Draw(img)
        
        # Add text "No Image Available"
        d.text((100,150), "No Image\nAvailable", fill='gray')
        
        # Save the image
        img.save(path)
    except Exception as e:
        print(f"Error creating placeholder: {str(e)}")

def process_csv_row(row, media_path):
    """Process a single CSV row and return product data."""
    try:
        # Convert flash_sale to boolean
        flash_sale = str(row.get('flash_sale', '')).lower() in ['true', '1', 'yes']
        
        # Handle product image with more flexibility
        product_picture = row.get('product_picture', '')
        
        if product_picture:
            if product_picture.startswith(('http://', 'https://')):
                # Handle remote URLs
                product_picture = download_image(product_picture, media_path)
            elif os.path.isfile(product_picture):
                # Handle local files
                filename = secure_filename(os.path.basename(product_picture))
                dest_path = os.path.join(media_path, filename)
                with open(product_picture, 'rb') as src, open(dest_path, 'wb') as dst:
                    dst.write(src.read())
                product_picture = os.path.join('./media', filename)
            else:
                # Use placeholder if path is invalid
                product_picture = get_placeholder_image_path()
        else:
            # Use placeholder if no image specified
            product_picture = get_placeholder_image_path()
                
        # Calculate discounted price
        current_price = float(row['current_price'])
        promotion_percentage = float(row.get('promotion_percentage', 0))
        discounted_price = current_price - (current_price * promotion_percentage / 100)
        
        return {
            'product_name': row['product_name'],
            'author': row['author'],
            'rating': float(row['rating']),
            'current_price': current_price,
            'in_stock': int(row['in_stock']),
            'flash_sale': flash_sale,
            'promotion_percentage': promotion_percentage,
            'discounted_price': discounted_price,
            'product_picture': product_picture,
            'category_id': int(row['category_id']),
            'subcategory_id': int(row['subcategory_id']),
            'warehouse_location': row.get('warehouse_location', 'Main Warehouse'),
            'low_stock_threshold': int(row.get('low_stock_threshold', 10))
        }
    except Exception as e:
        raise ValueError(f"Error processing row: {str(e)}")

def generate_csv_template():
    """Generate a template CSV file for bulk uploads."""
    template_data = {
        'product_name': ['Example Book 1', 'Example Book 2'],
        'author': ['Author 1', 'Author 2'],
        'rating': [4.5, 4.0],
        'current_price': [29.99, 19.99],
        'in_stock': [100, 50],
        'category_id': [1, 1],
        'subcategory_id': [1, 2],
        'promotion_percentage': [0, 10],
        'flash_sale': [False, True],
        'product_picture': ['', ''],  # Empty for placeholder images
        'warehouse_location': ['Main Warehouse', 'North Warehouse'],
        'low_stock_threshold': [10, 15]
    }
    
    df = pd.DataFrame(template_data)
    return df.to_csv(index=False)

@admin.route('/bulk-upload', methods=['GET', 'POST'])
@login_required
@admin_required
@check_permission('manage_products')
@limiter.limit("10 per hour") 
def bulk_upload():
    form = BulkUploadForm()
    
    if form.validate_on_submit():
        try:
            file = form.csv_file.data
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
                
            csv_content = StringIO(file.stream.read().decode("UTF8"))
            csv_reader = csv.DictReader(csv_content)
            
            # Validate headers
            if not validate_csv_headers(csv_reader.fieldnames):
                flash('Invalid CSV format. Please check the template.', 'error')
                return redirect(request.url)
                
            # Ensure media directory exists
            media_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media')
            os.makedirs(media_path, exist_ok=True)
            
            success_count = 0
            error_count = 0
            errors = []
            
            # Process each row
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    product_data = process_csv_row(row, media_path)
                    
                    # Create new product
                    new_product = Product(**product_data)
                    db.session.add(new_product)
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {row_num}: {str(e)}")
                    continue
                    
            # Commit all successful products
            try:
                db.session.commit()
                
                # Log the activity
                log_activity(
                    action='bulk_upload_products',
                    entity_type='product',
                    details={
                        'success_count': success_count,
                        'error_count': error_count,
                        'errors': errors[:10]  # Log first 10 errors
                    }
                )
                
                flash(f'Successfully uploaded {success_count} products. {error_count} failures.', 
                      'success' if error_count == 0 else 'warning')
                
            except Exception as e:
                db.session.rollback()
                flash(f'Database error: {str(e)}', 'error')
                
            # If there were errors, provide detailed feedback
            if errors:
                return render_template(
                    'bulk_upload_results.html',
                    success_count=success_count,
                    error_count=error_count,
                    errors=errors
                )
                
            return redirect(url_for('admin.shop_items'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(request.url)
            
    # GET request - show upload form
    return render_template('bulk_upload.html', form=form)

def generate_csv_template():
    """Generate a template CSV file for bulk uploads."""
    template_data = {
        'product_name': ['Example Book 1', 'Example Book 2'],
        'author': ['Author 1', 'Author 2'],
        'rating': [4.5, 4.0],
        'current_price': [29.99, 19.99],
        'in_stock': [100, 50],
        'category_id': [1, 1],
        'subcategory_id': [1, 2],
        'promotion_percentage': [0, 10],
        'flash_sale': [False, True],
        'product_picture': ['https://example.com/book1.jpg', 'https://example.com/book2.jpg'],
        'warehouse_location': ['Main Warehouse', 'North Warehouse'],
        'low_stock_threshold': [10, 15]
    }
    
    df = pd.DataFrame(template_data)
    return df.to_csv(index=False)

@admin.route('/download-template')
@login_required
@admin_required
def download_template():
    """Download a CSV template for bulk uploads."""
    template = generate_csv_template()
    return Response(
        template,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=bulk_upload_template.csv'}
    )