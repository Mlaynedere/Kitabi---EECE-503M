from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, PasswordField, EmailField, BooleanField, SubmitField, FileField, SelectField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired,NumberRange, ValidationError, length
from flask_wtf.file import FileAllowed

class SignUpForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), length(min=2)])
    email = EmailField('Email', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), length(min=2)])
    password1 = PasswordField('Enter Your Password', validators=[DataRequired(), length(min=8)])
    password2 = PasswordField('Confirm Your Password', validators=[DataRequired(), length(min=8)])
    submit = SubmitField('Sign Up')
    
    
class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Enter Your Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators = [DataRequired(), length(min=6)])
    new_password = PasswordField('Current Password', validators = [DataRequired(), length(min=6)])
    confirm_new_password = PasswordField('Current Password', validators = [DataRequired(), length(min=6)])
    change_password = SubmitField('Change Password')


class ShopItemsForm(FlaskForm):
    product_name = StringField('Book Title', validators=[
        DataRequired(message='Book title is required')
    ])
    
    author = StringField('Author', validators=[
        DataRequired(message='Author name is required')
    ])
    
    rating = FloatField('Rating', validators=[
        DataRequired(message='Rating is required'),
        NumberRange(min=0, max=5, message='Rating must be between 0 and 5')
    ])
    
    current_price = FloatField('Current Price', validators=[
        DataRequired(message='Price is required'),
        NumberRange(min=0, message='Price must be greater than 0')
    ])
    
    promotion_percentage = IntegerField('Promotion Percentage', validators=[
        NumberRange(min=0, max=100, message='Promotion must be between 0 and 100%')
    ], default=0)
    
    in_stock = IntegerField('In Stock', validators=[
        DataRequired(message='Stock quantity is required'),
        NumberRange(min=0, message='Stock quantity must be 0 or greater')
    ])
    
    product_picture = FileField('Product Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files are allowed!')
    ])
    
    flash_sale = BooleanField('Flash Sale')
    
    category = SelectField('Category', 
        coerce=int,
        validators=[DataRequired(message='Please select a category')]
    )
    
    subcategory = SelectField('Subcategory', 
        coerce=int,
        validators=[DataRequired(message='Please select a subcategory')]
    )
    
    add_product = SubmitField('Add Product')
    update_product = SubmitField('Update')

    def validate_promotion_percentage(self, field):
        if field.data < 0 or field.data > 100:
            raise ValidationError('Promotion percentage must be between 0 and 100')

class OrderForm(FlaskForm):
    order_status = SelectField('Order Status', choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'),
                                                        ('Out for delivery', 'Out for delivery'),
                                                        ('Delivered', 'Delivered'), ('Canceled', 'Canceled')])

    update = SubmitField('Update Status')

class InventoryForm(FlaskForm):
    warehouse_location = SelectField('Warehouse Location', 
        choices=[
            ('Main Warehouse', 'Main Warehouse'),
            ('North Warehouse', 'North Warehouse'),
            ('South Warehouse', 'South Warehouse')
        ]
    )
    low_stock_threshold = IntegerField('Low Stock Alert Threshold', 
        validators=[DataRequired(), NumberRange(min=1)],
        default=10
    )
    in_stock = IntegerField('Current Stock', 
        validators=[DataRequired(), NumberRange(min=0)]
    )
    update_stock = SubmitField('Update Stock')

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Length

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class RoleForm(FlaskForm):
    name = StringField('Role Name', 
        validators=[DataRequired(), Length(max=50)])
    
    description = TextAreaField('Description', 
        validators=[Length(max=200)])
    
    permissions = MultiCheckboxField('Permissions', 
        choices=[
            ('manage_products', 'Manage Products'),
            ('manage_orders', 'Manage Orders'),
            ('manage_users', 'Manage Users'),
            ('view_reports', 'View Reports'),
            ('manage_inventory', 'Manage Inventory'),
            ('manage_returns', 'Manage Returns')
        ])

class AssignRoleForm(FlaskForm):
    roles = SelectMultipleField('Roles', coerce=int)
    submit = SubmitField('Assign Roles')