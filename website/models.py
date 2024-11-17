from . import db, bcrypt
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class  Customer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique = True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)
    
    cart_items = db.relationship('Cart', backref=db.backref('customer', lazy=True))
    orders = db.relationship('Order', backref=db.backref('customer', lazy=True))
    
    
    @property
    def password(self):
        raise AttributeError('Password is not a readable Attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password=password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password=password)
    

    def __str__(self):
        return '<Customer %r>' % Customer.id 
    
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    product_name = db.Column(db.String(100), nullable = False)
    author = db.Column(db.String(100), nullable = False)
    rating = db.Column(db.Float, nullable = False)
    current_price = db.Column(db.Float, nullable = False)
    in_stock = db.Column(db.Integer, nullable = False)
    low_stock_threshold = db.Column(db.Integer, default=10)  # New field
    warehouse_location = db.Column(db.String(100), nullable=False, default='Main Warehouse')  # New field
    promotion_percentage = db.Column(db.Integer, default=0)  # New field for promotion
    discounted_price = db.Column(db.Float, nullable=True) 
    product_picture = db.Column(db.String(1000), nullable=False)
    flash_sale = db.Column(db.Boolean, default = False)
    date_added = db.Column(db.DateTime, default = datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('sub_category.id'), nullable=False)
    last_stock_update = db.Column(db.DateTime, default=datetime.utcnow)  # New field

    carts = db.relationship('Cart', backref=db.backref('product', lazy=True))
    orders = db.relationship('Order', backref=db.backref('product'), lazy=True)
    
    def __str__(self):
        return '<Product %r>' % self.id
 
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    quantity = db.Column(db.Integer, nullable=False)
    
    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable = False)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    def __str__(self):
        return '<Cart %r>' % self.id

    
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    payment_id = db.Column(db.String(1000), nullable=False)
    
    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    def __str__(self):
        return '<Order %r>' % self.id

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    products = db.relationship('Product', backref='category', lazy=True)

    subcategories = db.relationship('SubCategory', backref='category', lazy=True)

    def __str__(self):
        return f'<Category {self.name}>'


class SubCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    products = db.relationship('Product', backref='subcategory', lazy=True)

    def __str__(self):
        return f'<SubCategory {self.name}>'
    

class StockHistory(db.Model):
    __tablename__ = 'stock_history'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    previous_stock = db.Column(db.Integer, nullable=False)
    new_stock = db.Column(db.Integer, nullable=False)
    change = db.Column(db.Integer, nullable=False)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow)
    warehouse_location = db.Column(db.String(100), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

    product = db.relationship('Product', backref='stock_history', lazy=True)