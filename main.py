from website import create_app, db

app = create_app()

def init_db():
    with app.app_context():
        # Import all models here
        from website.models import Customer, Cart, Product, Order, Category, SubCategory, StockHistory
        
        # Create all tables
        db.create_all()
        
        # Now seed the database
        from website import seed_database
        seed_database()

if __name__ == '__main__':
    init_db()  # Initialize database before running app
    app.run(debug=True, port=4000)