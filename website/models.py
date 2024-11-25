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
    
    membership_tier_id = db.Column(db.Integer, db.ForeignKey('membership_tier.id'), default=1)  # Default to Normal
    points = db.Column(db.Integer, default=0)
    membership_tier = db.relationship('MembershipTier', backref='customers')

    def add_points(self, amount):
            """Add points based on purchase amount and tier multiplier"""
            points_earned = int(amount * self.membership_tier.points_multiplier)
            self.points += points_earned
            self.check_tier_upgrade()
        
    def check_tier_upgrade(self):
        """Check and upgrade membership tier based on points"""
        if self.points >= 10000 and self.membership_tier.name != 'Gold':
            gold_tier = MembershipTier.query.filter_by(name='Gold').first()
            self.membership_tier_id = gold_tier.id
        elif self.points >= 5000 and self.membership_tier.name == 'Normal':
            premium_tier = MembershipTier.query.filter_by(name='Premium').first()
            self.membership_tier_id = premium_tier.id

    cart_items = db.relationship('Cart', back_populates='customer', lazy=True)
    orders = db.relationship('Order', back_populates='customer', lazy=True)
    activity_logs = db.relationship('ActivityLog', back_populates='user', lazy=True)
    returns = db.relationship('Return', foreign_keys='Return.customer_link', back_populates='customer', lazy=True)

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
    returns = db.relationship('Return', foreign_keys='Return.product_link', back_populates='product', lazy=True)

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
    returns = db.relationship('Return', foreign_keys='Return.order_link', back_populates='order', lazy=True)
    delivery_fee = db.Column(db.Float, default=0.0)  # New field
    discount_applied = db.Column(db.Float, default=0.0)  # New field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # New field
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


class Return(db.Model):
    __tablename__ = 'returns'
    
    id = db.Column(db.Integer, primary_key=True)
    order_link = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    return_date = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected, completed
    resolution = db.Column(db.String(50))  # refund, replacement, rejected
    refund_amount = db.Column(db.Float)
    admin_notes = db.Column(db.Text)
    processed_by = db.Column(db.Integer, db.ForeignKey('customer.id'))
    processed_date = db.Column(db.DateTime)
    tracking_number = db.Column(db.String(100))
    replacement_order_id = db.Column(db.Integer, db.ForeignKey('order.id'))

    # Relationships
    order = db.relationship('Order', foreign_keys=[order_link], back_populates='returns')
    customer = db.relationship('Customer', foreign_keys=[customer_link], back_populates='returns')
    product = db.relationship('Product', foreign_keys=[product_link], back_populates='returns')
    admin = db.relationship('Customer', foreign_keys=[processed_by], backref='processed_returns')
    replacement_order = db.relationship('Order', foreign_keys=[replacement_order_id], backref='replacement_for')

class MembershipTier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Normal, Premium, Gold
    discount_percentage = db.Column(db.Float, default=0)
    free_delivery_threshold = db.Column(db.Float, nullable=True)  # NULL for Gold (always free)
    early_access = db.Column(db.Boolean, default=False)
    priority_support = db.Column(db.Boolean, default=False)
    points_multiplier = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)