from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, PasswordField, EmailField, BooleanField, SubmitField, FileField, DecimalField
from wtforms.validators import DataRequired, length, NumberRange

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
    product_name = StringField('Book Title', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    rating = FloatField('Rating', validators=[DataRequired(), NumberRange(min=0,max=5)])
    current_price = FloatField('Current Price', validators=[DataRequired()])
    promotion_percentage = IntegerField('Promotion Percentage', validators=[NumberRange(min=0, max=100)], default=0)
    in_stock = IntegerField('In Stock', validators=[DataRequired(), NumberRange(min=0)])
    product_picture = FileField('Product Picture', validators=[DataRequired()])
    flash_sale = BooleanField('Flash Sale')

    add_product = SubmitField('Add Product')
    update_product = SubmitField('Update')