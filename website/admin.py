from flask import Blueprint, render_template, flash, send_from_directory, redirect
from flask_login import login_required, current_user
from .forms import ShopItemsForm
from werkzeug.utils import secure_filename
from .models import Product
from . import db

admin = Blueprint('admin', __name__)

@admin.route('/media/<path:filename>')
def get_image(filename):
    return send_from_directory('../media', filename)

@admin.route('/add-shop-items', methods=['GET', 'POST'])
@login_required
def add_shop_items():
    if current_user.id == 1:
        form = ShopItemsForm()

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

            file_name = secure_filename(file.filename)

            file_path = f'./media/{file_name}'

            file.save(file_path)

            new_shop_item = Product()
            new_shop_item.product_name = product_name
            new_shop_item.author = author
            new_shop_item.rating = rating
            new_shop_item.current_price = current_price
            new_shop_item.in_stock = in_stock
            new_shop_item.flash_sale = flash_sale
            new_shop_item.promotion_percentage=promotion_percentage
            new_shop_item.discounted_price = discounted_price
            new_shop_item.product_picture = file_path

            try:
                db.session.add(new_shop_item)
                db.session.commit()
                flash(f'{product_name} added Successfully')
                print('Product Added')
                return render_template('add_shop_items.html', form=form)
            except Exception as e:
                print(e)
                flash('Product Not Added!!')

        return render_template('add_shop_items.html', form=form)

    return render_template('404.html')

@admin.route('/shop-items', methods=['GET', 'POST'])
@login_required
def shop_items():
    if current_user.id == 1:
        items = Product.query.order_by(Product.date_added).all()
        return render_template('shop_items.html', items=items)
    return render_template('404.html')

@admin.route('/update-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def update_item(item_id):
    if current_user.id == 1:
        form = ShopItemsForm()

        item_to_update = Product.query.get(item_id)

        form.product_name.data = item_to_update.product_name
        form.author.data = item_to_update.author
        form.rating.data = item_to_update.rating
        form.current_price.data = item_to_update.current_price
        form.in_stock.data = item_to_update.in_stock
        form.flash_sale.data = item_to_update.flash_sale
        form.promotion_percentage.data = item_to_update.promotion_percentage

        if form.product_picture.data:
            file = form.product_picture.data
            file_name = secure_filename(file.filename)
            file_path = f'./media/{file_name}'
            file.save(file_path)
        else:
            file_path = item_to_update.product_picture  # Keep the old image

        if form.validate_on_submit():
            product_name = form.product_name.data
            author = form.author.data
            rating = form.rating.data
            current_price = form.current_price.data
            in_stock = form.in_stock.data
            flash_sale = form.flash_sale.data
            promotion_percentage = form.promotion_percentage.data
            discounted_price = current_price - (current_price * promotion_percentage / 100)

            try:
                Product.query.filter_by(id=item_id).update(dict(
                    product_name=product_name,
                    author=author,
                    rating=rating,
                    current_price=current_price,
                    in_stock=in_stock,
                    flash_sale=flash_sale,
                    promotion_percentage=promotion_percentage,
                    discounted_price=discounted_price,
                    product_picture=file_path
                ))

                db.session.commit()
                flash(f'{product_name} updated Successfully')
                print('Product Updated')
                return redirect('/shop-items')
            except Exception as e:
                print('Product not Updated', e)
                flash('Item Not Updated!!!')

        return render_template('update_item.html', form=form)
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

@admin.route('/admin-page')
@login_required
def admin_page():
    if current_user.id == 1:
        return render_template('admin.html')
    return render_template('404.html')