from .models import User, get_todays_recent_posts, search_users
from flask import Flask, request, session, redirect, url_for, render_template, flash
import re

app = Flask(__name__)

@app.route('/')
def index():
    posts = get_todays_recent_posts()
    return render_template('index.html', posts=posts)

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

@app.route('/add_post', methods=['POST'])
def add_post():
    title = request.form['title']
    tags = request.form['tags']
    text = request.form['text']

    if not title:
        flash('You must give your post a title.')
    elif not tags:
        flash('You must give your post at least one tag.')
    elif not text:
        flash('You must give your post a text body.')
    else:
        User(session['username']).add_post(title, tags, text)

    return redirect(url_for('index'))

@app.route('/like_post/<post_id>')
def like_post(post_id):
    username = session.get('username')

    if not username:
        flash('You must be logged in to like a post.')
        return redirect(url_for('login'))

    User(username).like_post(post_id)

    flash('Liked post.')
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

    results = search_users(username)

    return render_template(
	    'search_results.html',
        results=results,
		username=username
    )
	#include profile picture here when it comes out
