from flask import Blueprint,render_template
from flask_login import login_required, current_user
from .models import Customer

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template('home.html')
# def home():
#     users = Customer.query.all()  # Query all users
#     if not users:  # Check if there are no users in the table
#         return "No users found in the database."  # Handle empty database case

    # Build a string with usernames of all users
    # usernames = ", ".join([user.username for user in users])
    # return f"Users in database: {usernames}"  # Return all usernames as a response