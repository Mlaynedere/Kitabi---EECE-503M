from . import db, bcrypt
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Association table for User-Role many-to-many relationship
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('customer.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

class Customer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)
    is_admin_val = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    
    cart_items = db.relationship('Cart', back_populates='customer', lazy=True)
    orders = db.relationship('Order', back_populates='customer', lazy=True)
    activity_logs = db.relationship('ActivityLog', back_populates='user', lazy=True)
    
    # Relationship with roles
    roles = db.relationship(
        'Role',
        secondary=user_roles,
        back_populates='users',
        lazy='dynamic'
    )
    @property
    def password(self):
        raise AttributeError('Password is not a readable Attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password=password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password=password)
    
    @property
    def is_admin(self):
        """Check if user has any admin roles"""
        return self.is_admin_val or any(
            role.name in ['Super Admin', 'Product Manager', 'Order Manager'] 
            for role in self.roles
        )
    
    @is_admin.setter
    def is_admin(self, value):
        """Set the is_admin value"""
        self.is_admin_val = value
    
    def has_permission(self, permission):
        """Check if user has specific permission through any of their roles"""
        if not self.roles:
            return False
        for role in self.roles:
            # No need to parse JSON as it's already the correct type
            permissions = role.permissions or []
            if permission in permissions:
                return True
        return False
    
    def has_role(self, role_name):
        """Check if user has specific role"""
        return any(role.name == role_name for role in self.roles)
    
    def __str__(self):
        return f'<Customer {self.username}>'

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    permissions = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship(
        'Customer',
        secondary=user_roles,
        back_populates='roles',
        lazy='dynamic'
    )
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    in_stock = db.Column(db.Integer, nullable=False)
    low_stock_threshold = db.Column(db.Integer, default=10)
    warehouse_location = db.Column(db.String(100), nullable=False, default='Main Warehouse')
    promotion_percentage = db.Column(db.Integer, default=0)
    discounted_price = db.Column(db.Float, nullable=True) 
    product_picture = db.Column(db.String(1000), nullable=False)
    flash_sale = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('sub_category.id'), nullable=False)
    last_stock_update = db.Column(db.DateTime, default=datetime.utcnow)

    carts = db.relationship('Cart', back_populates='product', lazy=True)
    orders = db.relationship('Order', back_populates='product', lazy=True)
    stock_history = db.relationship('StockHistory', back_populates='product', lazy=True)
    category = db.relationship('Category', back_populates='products')
    subcategory = db.relationship('SubCategory', back_populates='products')

    def __str__(self):
        return '<Product %r>' % self.id

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    customer = db.relationship('Customer', back_populates='cart_items')
    product = db.relationship('Product', back_populates='carts')
    
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
    
    customer = db.relationship('Customer', back_populates='orders')
    product = db.relationship('Product', back_populates='orders')
    
    def __str__(self):
        return '<Order %r>' % self.id

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    products = db.relationship('Product', back_populates='category', lazy=True)
    subcategories = db.relationship('SubCategory', back_populates='category', lazy=True)

    def __str__(self):
        return f'<Category {self.name}>'

class SubCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    products = db.relationship('Product', back_populates='subcategory', lazy=True)
    category = db.relationship('Category', back_populates='subcategories')

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

    product = db.relationship('Product', back_populates='stock_history')

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('Customer', back_populates='activity_logs')
