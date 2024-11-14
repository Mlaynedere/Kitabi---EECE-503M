from flask import Blueprint, render_template, flash, redirect, request, url_for
from .forms import LoginForm, SignUpForm
from .models import Customer
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            flash('Passwords do not match!', category='error')
            return redirect(url_for('auth.sign_up'))
        user = Customer.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        else:
            print(f"Creating new user: {email}, {username}")  # Debug: Log user details

            new_user = Customer(email=email, username=username)
            new_user.set_password(password)
            try:
                db.session.add(new_user)
                db.session.commit()
                print(f"User {username} successfully added.")  #
            # db.session.add(new_user)
            # db.session.commit()
            except Exception as e:
                print(f"Error saving user to database: {e}")  # Debug: Log any errors
                flash('An error occurred. Please try again.', category='error')
                return redirect(url_for('auth.sign_up'))
            user_check = Customer.query.filter_by(email=email).first()
            if user_check:
                print(f"User {user_check.username} found in database after sign-up.")  # Debug: Check user in DB
            else:
                print(f"User {email} not found in database after sign-up.")  # Debug: Missing user
            flash('Account created!', category='success')
            return redirect(url_for('auth.login'))
    return render_template('signup.html')
    # form = SignUpForm()
    # if form.validate_on_submit():
    #     email = form.email.data
    #     username = form.username.data
    #     password1 = form.password1.data
    #     password2 = form.password2.data

    #     if password1 == password2:
    #         new_customer = Customer()
    #         new_customer.email = email
    #         new_customer.username = username
    #         new_customer.password = password2
            
    #         try:
    #             db.session.add(new_customer)
    #             db.session.commit()
    #             flash('Account Created Successfully' + '\n' + 'You can now login!')
    #             return redirect('/login')
    #         except Exception as e:
    #             print(e)
    #             flash('Email already exists!')

    #         form.email.data = ''
    #         form.username.data = ''
    #         form.password1.data = ''
    #         form.password2.data = ''
            
    # return render_template('signup.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"Attempting login for email: {email}")  # Debug statement

        user = Customer.query.filter_by(email=email).first()
        if user:
            print("User found")
            if user.check_password(password):
                print("Password Verified")
                login_user(user)
                flash('Logged in successfully!', category='success')
                return redirect(url_for('views.home'))
            else:
                print("Password incorrect.")
                flash('Invalid credentials, please try again.', category='error')
        else:
            print("User not found.")
            flash("Email not registered. Please sign up first", category='error')     
    return render_template('login.html')
    # form = LoginForm()
    # if form.validate_on_submit():
    #     email = form.email.data
    #     password = form.password.data
        
    #     customer = Customer.query.filter_by(email=email).first()

    #     if customer:
    #         if customer.verify_password(password=password):
    #             login_user(customer)
    #             redirect('/')
    #         else:
    #             flash('Incorrect Email or Password!')
    #     else:
    #         flash('Account does not exist, please sign up!')
    # return render_template('login.html', form=form)

@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def log_out():
    logout_user()
    flash('Logged out successfully.', category='success')
    return redirect('/')