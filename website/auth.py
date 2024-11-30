from flask import Blueprint, render_template, flash, redirect, request, url_for, jsonify
from flask_limiter import Limiter
from .forms import LoginForm, SignUpForm, PasswordChangeForm
from .models import Customer, MembershipTier
from . import db, limiter
from flask_login import login_user, login_required, logout_user, current_user
from .utils import get_categories_dict
from .security import password_meets_requirements, sanitize_input
from werkzeug.security import check_password_hash
from .jwt_utils import create_access_token

auth = Blueprint('auth', __name__)

@auth.route('/sign-up', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Add rate limiting
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))

    form = SignUpForm()
    if form.validate_on_submit():
        # Sanitize inputs
        full_name = sanitize_input(form.full_name.data)
        email = sanitize_input(form.email.data)
        username = sanitize_input(form.username.data)
        password1 = form.password1.data
        password2 = form.password2.data

        # Check password strength
        is_valid, msg = password_meets_requirements(password1)
        if not is_valid:
            flash(msg, 'error')
            return redirect(url_for('auth.sign_up'))

        existing_user = Customer.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists!', 'error')
            return redirect(url_for('auth.sign_up'))

        existing_username = Customer.query.filter_by(username=username).first()
        if existing_username:
            flash('Username already taken!', 'error')
            return redirect(url_for('auth.sign_up'))
        
        if password1 == password2:
            # Get the default "Normal" tier
            normal_tier = MembershipTier.query.filter_by(name='Normal').first()
            
            # If Normal tier doesn't exist, create it
            if not normal_tier:
                normal_tier = MembershipTier(
                    name='Normal',
                    discount_percentage=0,
                    free_delivery_threshold=None,
                    early_access=False,
                    priority_support=False,
                    points_multiplier=1.0
                )
                db.session.add(normal_tier)
                try:
                    db.session.commit()
                except Exception as e:
                    print(f"Error creating Normal tier: {e}")
                    db.session.rollback()
                    flash('Error during signup. Please try again.', 'error')
                    return redirect(url_for('auth.sign_up'))

            # Create new customer with the Normal tier
            new_customer = Customer()
            new_customer.full_name = full_name
            new_customer.email = email
            new_customer.username = username
            new_customer.password = password2
            new_customer.points = 0
            new_customer.membership_tier_id = normal_tier.id
            
            try:
                db.session.add(new_customer)
                db.session.commit()
                flash('Account Created Successfully')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                print(f"Error creating account: {e}")
                flash('There was an error creating your account. Please try again later.', 'error')
                return redirect(url_for('auth.sign_up'))
    
    return render_template('signup.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    form = LoginForm()
    if request.method == 'GET':
        return render_template('login.html', form=form)
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        user = Customer.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            # Log in the user and generate a JWT token
            login_user(user)
            access_token = create_access_token(user_id=user.id)

            # Check the user's role for redirection
            roles = [role.name.lower() for role in user.roles]
            redirect_url = url_for('admin.admin_page') if any(role in ['super admin', 'product manager', 'order manager'] for role in roles) else url_for('views.home')
            response = jsonify({
                'message': 'Logged in successfully!',
                'Authorization': access_token,
                'redirect_url': redirect_url
            })
            # Set token in cookie as well
            response.set_cookie(
                'jwt_token',
                access_token,
                httponly=True,
                secure=True,
                samesite='Strict'
            )
            return response, 200
        else:
            return jsonify({'error': 'Invalid credentials, please try again.'}), 401

    return jsonify({'error': 'Invalid form submission.'}), 400

@auth.route('/logout', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
@login_required
def log_out():
    logout_user()
    flash('Logged out successfully.', category='success')
    return redirect('/')

@auth.route('/account/<int:user_id>')
@limiter.limit("30 per minute")
@login_required
def account(user_id):
    user = Customer.query.get(user_id)
    return render_template('account.html', 
                         current_user=user,
                         categories=get_categories_dict())

@auth.route('/change-password/<int:user_id>', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
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
                is_valid, msg = password_meets_requirements(new_password)
                if not is_valid:
                    flash(msg, 'error')
                    return redirect(url_for('auth.change_password', user_id=user.id))
                

                user.password = confirm_new_password
                db.session.commit()
                flash('Password Updated Successfully')
                return redirect(f'/account/{user.id}')
            else:
                flash('New Passwords do not match!!')

        else:
            flash('Current Password is Incorrect')

    return render_template('change_password.html', form=form, categories=get_categories_dict())