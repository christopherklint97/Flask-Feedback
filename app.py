from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError
from os import environ

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


connect_db(app)
db.create_all()
toolbar = DebugToolbarExtension(app)


@app.route('/')
def home_page():
    """ Redirect to login """
    try:
        username = session['username']
        return redirect(f'/users/{username}')

    except KeyError:
        return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """ Register user """

    form = RegisterForm()
    if form.validate_on_submit():

        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        # Bcrypt password
        new_user = User.register(
            username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken.  Please pick another')
            return render_template('register.html', form=form)
        session['username'] = username
        flash('User Created!', 'success')
        return redirect(f'/users/{username}')

    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """ Login user. """
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}!", "primary")
            session['username'] = username
            return redirect(f'/users/{username}')
        else:
            form.username.errors = ['Invalid username/password.']

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_user():
    """ Logout user """
    session.pop('username')
    flash("Goodbye!", "info")
    return redirect('/')


@app.route('/users/<username>')
def show_userinfo(username):
    """ Show userinfo if logged in. """
    try:
        if session['username'] == username:
            user = User.query.get_or_404(username)
            return render_template('user_info.html', user=user)
        else:
            flash("You do not have access to this user", "alert")
            return redirect('/login')

    except KeyError:
        return redirect('/login')


@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """ Delete user """
    try:
        if session['username'] == username:
            user = User.query.get_or_404(username)
            db.session.delete(user)
            db.session.commit()
            session.pop('username')
            return redirect('/')
        else:
            flash("You do not have access to this user", "alert")
            return redirect('/login')

    except KeyError:
        return redirect('/login')


@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    """ Add feedback. """
    try:
        if session['username'] == username:
            form = FeedbackForm()
            if form.validate_on_submit():
                title = form.title.data
                content = form.content.data
                feedback = Feedback(
                    title=title, content=content, username=username)
                db.session.add(feedback)
                db.session.commit()
                return redirect(f'/users/{username}')

            return render_template('add_feedback.html', form=form)
        else:
            flash("You do not have access to this feedback", "alert")
            return redirect('/login')

    except KeyError:
        return redirect('/login')


@app.route('/feedback/<feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    """ Update feedback. """
    try:
        feedback = Feedback.query.get_or_404(feedback_id)
        if session['username'] == feedback.username:
            title = feedback.title
            content = feedback.content
            form = FeedbackForm(title=title, content=content)
            if form.validate_on_submit():
                feedback.title = form.title.data
                feedback.content = form.content.data
                db.session.add(feedback)
                db.session.commit()
                return redirect(f'/users/{feedback.username}')

            return render_template('update_feedback.html', form=form, feedback=feedback)
        else:
            flash("You do not have access to this feedback", "alert")
            return redirect('/login')

    except KeyError:
        return redirect('/login')


@app.route('/feedback/<feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    """ Update feedback. """
    try:
        feedback = Feedback.query.get_or_404(feedback_id)
        if session['username'] == feedback.username:
            db.session.delete(feedback)
            db.session.commit()

            return redirect(f'/users/{feedback.username}')

        else:
            flash("You do not have access to this feedback", "alert")
            return redirect('/login')

    except KeyError:
        return redirect('/login')
