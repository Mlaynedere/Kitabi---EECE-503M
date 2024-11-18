from flask import Blueprint, render_template, flash, redirect, request, url_for
from .forms import LoginForm, SignUpForm, PasswordChangeForm
from .models import Customer
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from .utils import get_categories_dict
auth = Blueprint('auth', __name__)


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))

    form = SignUpForm()
    if form.validate_on_submit():
        full_name = form.full_name.data
        email = form.email.data
        username = form.username.data
        password1 = form.password1.data
        password2 = form.password2.data

        existing_user = Customer.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists!', 'error')
            return redirect(url_for('auth.sign_up'))

        existing_username = Customer.query.filter_by(username=username).first()
        if existing_username:
            flash('Username already taken!', 'error')
            return redirect(url_for('auth.sign_up'))
        
        if password1 == password2:
            new_customer = Customer()
            new_customer.full_name = full_name
            new_customer.email = email
            new_customer.username = username
            new_customer.password = password2
            try:
                db.session.add(new_customer)
                db.session.commit()
                flash('Account Created Successfully')
                return redirect(url_for('auth.login'))
            except Exception as e:
                flash('There was an error creating your account. Please try again later.', 'error')
                return redirect(url_for('auth.sign_up'))
        
    return render_template('signup.html', form=form)

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
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        user = Customer.query.filter_by(email=email).first()
        if user:
            if user.check_password(password=password):
                login_user(user)
                flash('Logged in successfully!', category='success')
                return redirect(url_for('views.home'))
            else:
                flash('Invalid credentials, please try again.', category='error')
        else:
            flash('Email not registered. Please sign up first.', category='error')
    
    return render_template('login.html', form=form)
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

@auth.route('/account/<int:user_id>')
@login_required
def account(user_id):
    user = Customer.query.get(user_id)
    return render_template('account.html', 
                         current_user=user,
                         categories=get_categories_dict())

@auth.route('/change-password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    form = PasswordChangeForm()
    user = Customer.query.get(user_id)
    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        confirm_new_password = form.confirm_new_password.data

        if user.check_password(current_password):
            if new_password == confirm_new_password:
                user.password = confirm_new_password
                db.session.commit()
                flash('Password Updated Successfully')
                return redirect(f'/account/{user.id}')
            else:
                flash('New Passwords do not match!!')

        else:
            flash('Current Password is Incorrect')

    return render_template('change_password.html', form=form, categories=get_categories_dict())