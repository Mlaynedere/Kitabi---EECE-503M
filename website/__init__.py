from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
import os

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
DB_NAME = 'database.sqlite3'

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
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html')
    
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

    return app