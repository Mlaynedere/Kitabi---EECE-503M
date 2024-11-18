from .models import Category

def get_categories_dict():
    """Helper function to get categories dictionary"""
    categories_dict = {}
    categories = Category.query.all()
    for category in categories:
        subcategories = [subcategory.name for subcategory in category.subcategories]
        categories_dict[category.name] = subcategories
    return categories_dict