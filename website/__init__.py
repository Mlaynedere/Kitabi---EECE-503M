import json
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, CSRFError
from datetime import datetime, timedelta
import os

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
DB_NAME = 'database.sqlite3'
TokenExpiryTime = 30 # Time in minutes for JWT to expire
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
def create_initial_roles():
    from .models import Role
    
    # Check if roles already exist
    if Role.query.first() is not None:
        print("Roles already initialized.")
        return
        
    roles = [
        {
            'name': 'Super Admin',
            'permissions': ['manage_products', 'manage_orders', 'manage_users', 
                          'view_reports', 'manage_inventory', 'manage_returns']
        },
        {
            'name': 'Product Manager',
            'permissions': ['manage_products', 'manage_inventory']
        },
        {
            'name': 'Order Manager',
            'permissions': ['manage_orders', 'manage_returns']
        }
    ]
    
    try:
        for role_data in roles:
            role = Role(
                name=role_data['name'],
                permissions=json.dumps(role_data['permissions'])
            )
            db.session.add(role)
        
        db.session.commit()
        print("Initial roles created successfully!")
    except IntegrityError:
        db.session.rollback()
        print("Roles already exist.")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating initial roles: {e}")

def create_super_admin():
    from .models import Customer, Role
    
    # Check if super admin exists
    if Customer.query.filter_by(email='admin@kitabi.com').first():
        print("Super Admin already exists.")
        return
        
    try:
        # Get the Super Admin role
        super_admin_role = Role.query.filter_by(name='Super Admin').first()
        if not super_admin_role:
            print("Super Admin role not found. Please run create_initial_roles first.")
            return
            
        # Create the super admin user
        super_admin = Customer(
            full_name='Admin User',
            email='admin@kitabi.com',
            username='admin',
            is_admin_val=True
        )
        super_admin.password = 'admin123456'
        super_admin.roles = [super_admin_role]
        
        db.session.add(super_admin)
        db.session.commit()
        print("Super Admin created successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating Super Admin: {e}")

def seed_database():
    from .models import Category, SubCategory
    
    # Check if database is already seeded
    if Category.query.first() is not None:
        print("Database already seeded.")
        return

    # Categories and subcategories for the online bookstore
    categories = {
        "Fiction": ["Fantasy", "Mystery", "Romance", "Science Fiction", "Historical Fiction"],
        "Non-Fiction": ["Biography", "Self-Help", "Science", "History", "True Crime"],
        "Children's Books": ["Picture Books", "Young Adult", "Educational", "Bedtime Stories", "Activity Books"],
        "Academic & Education": ["Textbooks", "Study Guides", "Research Papers", "Language Learning", "Professional Certifications"],
        "Comics & Graphic Novels": ["Superhero", "Manga", "Graphic Memoirs", "Science Fiction & Fantasy", "Comedy"],
        "Arts & Photography": ["Art History", "Photography Guides", "Drawing & Painting", "Performing Arts", "Architecture"],
        "Health & Wellness": ["Nutrition", "Fitness", "Mental Health", "Alternative Medicine", "Yoga & Meditation"],
        "Cookbooks & Food": ["Regional Cuisine", "Baking", "Vegetarian & Vegan", "Quick & Easy Recipes", "Wine & Spirits"],
        "Travel & Adventure": ["Travel Guides", "Memoirs", "Outdoor Survival", "Road Trips", "World Cultures"],
        "Business & Technology": ["Entrepreneurship", "Personal Finance", "Marketing", "Programming", "Leadership"],
    }

    try:
        for category_name, subcategories in categories.items():
            # Create category
            category = Category(name=category_name)
            db.session.add(category)
            db.session.flush()  # Get the ID without committing

            # Create subcategories
            for subcategory_name in subcategories:
                subcategory = SubCategory(
                    name=subcategory_name,
                    category_id=category.id
                )
                db.session.add(subcategory)

        db.session.commit()
        print("Database seeded successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding database: {e}")
def create_membership_tiers():
    """Initialize the default membership tiers"""
    from .models import MembershipTier
    
    # Check if tiers already exist
    if MembershipTier.query.first() is not None:
        print("Membership tiers already initialized.")
        return
        
    tiers = [
        {
            'name': 'Normal',
            'discount_percentage': 0,
            'free_delivery_threshold': 100,  # Free delivery over $100
            'early_access': False,
            'priority_support': False,
            'points_multiplier': 1.0
        },
        {
            'name': 'Premium',
            'discount_percentage': 5,
            'free_delivery_threshold': 50,  # Free delivery over $50
            'early_access': True,
            'priority_support': False,
            'points_multiplier': 1.5
        },
        {
            'name': 'Gold',
            'discount_percentage': 10,
            'free_delivery_threshold': None,  # Always free delivery
            'early_access': True,
            'priority_support': True,
            'points_multiplier': 2.0
        }
    ]
    
    try:
        for tier_data in tiers:
            tier = MembershipTier(**tier_data)
            db.session.add(tier)
        
        db.session.commit()
        print("Membership tiers created successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating membership tiers: {e}")

def create_app():
    app = Flask(__name__)
    from .models import Customer
    from .security import safe_query
    from .views import views
    from .admin import admin
    from .auth import auth
    
    app.config['SECRET_KEY'] = '09a2d47b626ac15b9328cd8268d6754b1e84c212637427859dd18570b94ddec10c6bf2731c93d0121fb9343e4c3ed632905300c507f3f06ab89b0776cc648bdad3f0fe77ca9a270d2e318f7dd0202afddce32c914daaf7a5dff44039182748da2b857c45a7063c18f15e46031d369909db05d933e804f921e3316ee97c38adae079da8f1f8d9763fc66cf8a11802f56e4fa5cf12c1e4aa32fb0a3591fbbbf268c24cc12883dd2bba75ecc2894903d8e548db6cba8f25d9978e6052d2d74b7cccb2b91280c3947fce0652e77396c28c91812d7016ccb3ec07719b9bdf40e095f1537ac41ca8329a2a2363e997a2e8efddbc49b02108e964e6f3c816201d047f4b'
    app.config['WTF_CSRF_SECRET_KEY'] = 'uysdguy&*%)*719640`9631gfsdljkfbhq289p74198-4610hjidb7^*&580&^^%)&%(#rogl:i!fydBSUI;T78TP189YTE72)' #Secret Key to sign the CSRF token
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30)
    )

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('csrf_error.html', reason=e.description), 400
    
    @app.template_filter('from_json')
    def from_json(value):
        try:
            return json.loads(value)
        except:
            return []

    @app.template_filter('tojson')
    def to_json(value):
        return json.dumps(value)
    
    @app.after_request
    def set_security_headers(response):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    @app.after_request
    def set_csp_header(response):
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
            "style-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "  # Allow self-hosted and inline images
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com data:; "  # Allow fonts from cdnjs, Google Fonts, and inline
            "object-src 'none'; "  # Disallow plugins
            "frame-ancestors 'self'; "  # Prevent clickjacking by allowing only self
            "base-uri 'self'; "  # Prevent <base> tag from being manipulated
            "form-action 'self';"  # Restrict form submissions to the same origin
        )
        response.headers['Content-Security-Policy'] = csp_policy
        return response


    
    
    @app.template_filter('time_ago')
    def time_ago(dt):
        now = datetime.utcnow()
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours} hour{"s" if hours != 1 else ""} ago'
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f'{days} day{"s" if days != 1 else ""} ago'
        else:
            return dt.strftime('%Y-%m-%d %H:%M')
    
    limiter.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return Customer.query.get(int(id))

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/')
    
    # Create database tables and initialize data
    with app.app_context():
        db.create_all()
        create_membership_tiers()
        seed_database()
        create_initial_roles()
        create_super_admin()

    return app
