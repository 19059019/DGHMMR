from .models import User, get_todays_recent_posts, search_users, valid_file, update_profile, update_icon, get_questions, get_answers, get_followed_questions, get_followed_answers
from passlib.hash import bcrypt
from flask import Flask, request, session, redirect, url_for, render_template, flash
import re
import os
from werkzeug import secure_filename

app = Flask(__name__)

ICON_FOLDER = 'blog/static/icons/'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        matchUser = re.match(r"^([A-Z][A-Za-z0-9].{3,13})$", username, flags=0)
        matchPass = re.match(r"^((?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,})$", password, flags=0)

        if not matchUser:
            flash('Your username must start with a capital and consist of only letters and digits')
        elif not matchPass:
            flash('Your password must be longer than 8 characters and contain one or more of the following: digit, lower-case letter and upper-case letter')
        elif not User(username).register(password):
            flash('A user with that username already exists.')
        else:
            session['username'] = username
            flash('Logged in.')
            return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not User(username).verify_password(password):
            flash('Invalid login.')
        else:
            session['username'] = username
            flash('Logged in.')
            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out.')
    return redirect(url_for('index'))

@app.route('/add_question', methods=['POST'])
def add_question():
    title = request.form['title']
    #tags = request.form['tags']
    text = request.form['text']

    if not title:
        flash('You must give your question a title.')
    #elif not tags:
    #    flash('You must give your post at least one tag.')
    elif not text:
        flash('You must give your question a text body.')
    else:
        User(session['username']).add_question(title, text)

    return redirect(url_for('questions'))

@app.route('/add_answer', methods=['POST'])
def add_answer():
    text = request.form['text']
    questionID = request.form['questionID']

    if not text:
        flash('You must give your answer a text body.')
    else:
        pass
        User(session['username']).add_answer(questionID, text)

    return redirect(url_for('questions'))

@app.route('/upvote_answer/<answer_id>')
def upvote_answer(answer_id):
    username = session.get('username')

    if not username:
        flash('You must be logged in to upvote an answer.')
        return redirect(url_for('login'))

    User(username).upvote_answer(answer_id)

    flash('Upvoted answer.')
    return redirect(request.referrer)

@app.route('/bookmark_question/<question_id>')
def bookmark_question(question_id):
    username = session.get('username')

    if not username:
        flash('You must be logged in to bookmark a question.')
        return redirect(url_for('login'))

    User(username).bookmark_question(question_id)

    flash('Bookmarked question.')
    return redirect(request.referrer)

@app.route('/follow_user/<user_name>')
def follow_user(user_name):
	username = session.get('username')

	if not username:
		flash('You must be logged in to follow someone.')

	User(username).follow_user(user_name)

	flash('following')
	return redirect(request.referrer)

@app.route('/profile/<username>')
def profile(username):
    logged_in_username = session.get('username')
    user_being_viewed_username = username

    user_being_viewed = User(user_being_viewed_username)
    posts = user_being_viewed.get_recent_posts()

    similar = []
    common = []

    if logged_in_username:
        logged_in_user = User(logged_in_username)

        if logged_in_user.username == user_being_viewed.username:
            similar = logged_in_user.get_similar_users()
        else:
            common = logged_in_user.get_commonality_of_user(user_being_viewed)

    bio = user_being_viewed.get_bio()
    icon = user_being_viewed.get_icon()

    return render_template(
        'profile.html',
        username=username,
        posts=posts,
        similar=similar,
        common=common,
        bio=bio,
        icon=icon
    )

@app.route('/search', methods=['GET', 'POST'])
def search():
    username = request.form['username']
    results = search_users(username, session.get('username'))

    return render_template(
	    'search_results.html',
        results=results,
		username=username,
    )

@app.route('/suggested_users/<username>', methods=['GET', 'POST'])
def suggested_users(username):
    logged_in_user = User(username)
    suggested = logged_in_user.get_suggested_users()

    return render_template(
	    'suggested_users.html',
        suggested=suggested
    )

@app.route('/profile/<username>/edit', methods=['GET','POST'])
def edit_profile(username):
    user = User(username)
    if request.method == 'POST':
        if 'icon' in request.files:
            icon = request.files['icon']
            icon_name = secure_filename(icon.filename)
            password = request.form['pass']
            if not valid_file(icon.filename):
                flash('File name not accepted')
            elif not user.verify_password(password):
                flash('Incorrect Password')
            elif not icon.save(os.path.join(ICON_FOLDER, icon_name)):
                update_icon(username, icon_name)
                return profile(username)
            else:
                flash("file upload failure")
        else:
            bio = request.form['bio']
            pass_old = request.form['pass_old']
            pass_new = request.form['pass_new']
            pass_new_confirm = request.form['pass_new_confirm']
            if pass_new == "":
                password = bcrypt.encrypt(pass_old)
                pass_new_confirm = pass_old
                pass_new = pass_old
            else:
                password = bcrypt.encrypt(pass_new)

            if not user.verify_password(pass_old):
                flash('Incorrect Password')
            elif pass_new_confirm != pass_new:
                flash("New Passwords don't match")
            elif not re.match(r"^((?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,})$", pass_new, flags=0):
                flash('Your new password must be longer than 8 characters and contain one or more of the following: digit, lower-case letter and upper-case letter')
            else:
                update_profile(username, bio, password)
                return profile(username)
    return render_template('edit_profile.html',
    username=username,
    bio=user.get_bio(),
    icon=user.get_icon())

@app.route('/profile/<username>/change_icon', methods=['GET','POST'])
def change_icon(username):
    user = User(username)
    if request.method == 'POST':
        if 'icon' in request.files:
            icon = request.files['icon']
            icon_name = secure_filename(icon.filename)
            password = request.form['pass']
            if not valid_file(icon.filename):
                flash('File name not accepted')
            elif not user.verify_password(password):
                flash('Incorrect Password')
            elif not icon.save(os.path.join(ICON_FOLDER, icon_name)):
                update_icon(username, icon_name)
                return profile(username)
            else:
                flash("file upload failure")
        else:
            bio = request.form['bio']
            pass_old = request.form['pass_old']
            pass_new = request.form['pass_new']

            pass_new_confirm = request.form['pass_new_confirm']
            if pass_new == "":
                password = bcrypt.encrypt(pass_old)
                pass_new_confirm = pass_old
                pass_new = pass_old
            else:
                password = bcrypt.encrypt(pass_new)

            if not user.verify_password(pass_old):
                flash('Incorrect Password')
            elif pass_new_confirm != pass_new:
                flash("New Passwords don't match")
            elif not re.match(r"^((?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,})$", pass_new, flags=0):
                flash('Your new password must be longer than 8 characters and contain one or more of the following: digit, lower-case letter and upper-case letter')
            else:
                update_profile(username, bio, password)
                return profile(username)
    return render_template('change_icon.html',
    username=username,
    icon=user.get_icon())

@app.route('/profile/<username>/bookmarks', methods=['GET','POST'])
def bookmarks(username):
    user = User(username)
    posts = user.get_bookmark()

    return render_template('bookmarks.html', username=username, posts=posts)

@app.route('/profile/<username>/followers', methods=['GET','POST'])
def followers(username):
    user = User(username)
    user2 = user.get_followers()

    return render_template('followers.html', username=username, user2 =user2)

@app.route('/questions', methods=['GET', 'POST'])
def questions():
    questions = get_questions()
    return render_template('questions.html', questions=questions)

@app.route('/followed_questions', methods=['GET', 'POST'])
def followed_questions():
    questions = get_followed_questions(session['username'])
    return render_template('questions.html', questions=questions)

@app.route('/followed_answers', methods=['GET', 'POST'])
def followed_answers():
    answers = get_followed_answers(session['username'])
    return render_template('see_followed_answers.html', answers=answers)
