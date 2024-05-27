from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, Collectors
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

# Connect to __init__
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=["GET", "POST"])
def login():
    title = "Login"
    if request.method == "POST":
        # Get input from form
        email = request.form.get("email")
        password = request.form.get("password")
        # Query email in database
        user = User.query.filter_by(email=email).first()
        # Check input is correct. If success login user and return home. If error send error message
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)  # login user
                # Return homepage
                return redirect(url_for('filter.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')
    # Return HTML page
    return render_template("login.html", user=current_user, title=title)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=["GET", "POST"])
@login_required
def sign_up():
    title = "Sign up"
    entomologists = Collectors.query.all()
    if request.method == "POST":
        email = request.form.get("email")
        initials = request.form.get("initials")
        entomologist_name = request.form.get("entomologist")
        institutionCode = request.form.get("institutionCode")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        user = User.query.filter_by(email=email).first()
        initials_test = User.query.filter_by(initials=initials).first()
        if user:
            flash('Email aready exists', category='error')
        elif len(email) < 4:
            pass
            flash("Email must be greater than 3 characters.", category="error")
        elif initials_test:
            pass
            flash('Initials aready exists', category='error')
        elif len(initials) != 3:
            pass
            flash("Initials must be 3 characters.", category="error")
        elif entomologist_name is None:
            pass
            flash("Select user name from list of entomologists.", category="error")
        elif password1 != password2:
            pass
            flash("Passwords don\'t match.", category="error")
        elif len(password1) < 6:
            pass
            flash("Password must be at least 6 characters.", category="error")
        else:
            # Add user to database
            new_user = User(email=email, initials=initials, password=generate_password_hash(
                password1, method='sha256'), entomologist_name=entomologist_name, institutionCode=institutionCode, createdByUserID=current_user.id)
            db.session.add(new_user)
            db.session.commit()
            user = User.query.filter_by(email=email).first()
            # login_user(user, remember=True) # login user
            flash("Account created!", category="success")
    return render_template("sign_up.html", user=current_user, title=title, entomologists=entomologists)


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    title = 'Change Password'
    if request.method == "POST":
        new_password1 = request.form.get("new_password1")
        new_password2 = request.form.get("new_password2")
        # Check that password is not similar to previous password
        if new_password1 != new_password2:
            pass
            flash("Passwords don\'t match.", category="error")
        elif len(new_password1) < 6:
            pass
            flash("Password must be at least 6 characters.", category="error")
        elif check_password_hash(current_user.password, new_password1):
            pass
            flash("This is the old password!", category="error")
        else:
            # Add new password to database
            current_user.password = generate_password_hash(
                new_password1, method='sha256')
            db.session.commit()
            flash("Password changed!", category="success")
            return redirect(url_for('entomologist.home'))  # Return homepage
    return render_template("change_password.html", user=current_user, title=title)
