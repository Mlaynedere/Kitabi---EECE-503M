import json
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import os

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
DB_NAME = 'database.sqlite3'

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

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test12345'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    @app.template_filter('from_json')
    def from_json(value):
        try:
            return json.loads(value)
        except:
            return []

    @app.template_filter('tojson')
    def to_json(value):
        return json.dumps(value)
    
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
        
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(id):
        from .models import Customer
        return Customer.query.get(int(id))
    
    # Register blueprints
    from .views import views
    from .auth import auth
    from .admin import admin
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/')
    
    # Create database tables and initialize data
    with app.app_context():
        db.create_all()
        seed_database()
        create_initial_roles()
        create_super_admin()

    return app
