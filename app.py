import os

from flask import Flask, render_template, request, flash, redirect, session, g, abort
# from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, UserEditForm
from models import db, connect_db, User, Progress

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'sqlite:///english_site.sqlite'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
# toolbar = DebugToolbarExtension(app)

connect_db(app)
db.create_all()


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    do_logout()
    flash('logout successful')
    return redirect('/login')


    # IMPLEMENT THIS


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)
    progress=Progress.query.filter_by(user_id=user.id).first()
    return render_template('users/show.html', user=user,progress=progress)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")

@app.route('/users/<int:user_id>/likes', methods=["GET"])
def show_likes(user_id):
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/likes.html', user=user, likes=user.likes)

@app.route('/messages/<int:message_id>/like', methods=['POST'])
def add_like(message_id):
    """Toggle a liked message for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    liked_message = Message.query.get_or_404(message_id)
    if liked_message.user_id == g.user.id:
        return abort(403)

    user_likes = g.user.likes

    if liked_message in user_likes:
        g.user.likes = [like.id for like in user_likes if like != liked_message]
    else:
        g.user.likes.append(liked_message)

    db.session.commit()
    print(g.user.likes)
    print('dasfdasfkndsafnaksdlngksan')
    return redirect("/")



@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = g.user
    form = UserEditForm(obj=user)

    if form.validate_on_submit():
        if User.authenticate(user.username, form.password.data):
            user.username = form.username.data
            user.email = form.email.data
            user.image_url = form.image_url.data or "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQUDAr2Zy9ZAs8KhMkc91DlHzoqFuLfXaZ1wFL9Iqr2k7iEfL0U6r8mG3i48HBecICyiDE&usqp=CAU"
            user.header_image_url = form.header_image_url.data or "https://new.mospolytech.ru/upload/iblock/f7d/student-privacy4.jpg"

            db.session.commit()
            return redirect(f"/users/{user.id}")

        flash("Wrong password, please try again.", 'danger')
        
    return render_template('users/edit.html',form=form)



@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")

@app.route('/video')

def watch_video():
    user = g.user
    return render_template('watch-video.html',user=user)


@app.route('/grammar-book')
def read_grammar_book():
    user = g.user
    return render_template('grammar-book.html',user=user)


@app.route('/story-book')
def read_story_book():
    user = g.user
    return render_template('story-book.html',user=user)

@app.route('/quiz')
def take_quiz():
    user = g.user
    return render_template('quiz.html',user=user)

@app.route('/submit-quiz',methods=['POST'])
def submit_quiz():
    points = 0;
    try:
        if request.form['q1'] == 'r4':
            points += 1
    
        if request.form['q2'] == 'r1':
            points += 1

        if request.form['q3'] == 'r1':
            points += 1

        if request.form['q4'] == 'r2':
            points += 1

        if request.form['q5'] == 'r2':
            points += 1

        print(points)
    except:
        return redirect('/quiz')
    user = g.user
    quiz_progress = Progress.query.filter_by(user_id = user.id).first()
    print(quiz_progress)
    if not quiz_progress:
        progress_db = Progress(
            user_id = user.id,
            quiz_score = points,
            is_grammar_book_completed = False,
            is_story_book_completed = False,
            is_video_completed = False
        )
        db.session.add(progress_db)
        db.session.commit()

    else: 
        quiz_progress.quiz_score = points
        db.session.commit()

    return render_template('submit-quiz.html',user=user,points=points)




@app.route('/grammar-book-completed')
def grammar_book_completed():
    
    user = g.user
    progress = Progress.query.filter_by(user_id = user.id).first()
    if not progress:
        progress_db = Progress(
            user_id = user.id,
            quiz_score = 0,
            is_grammar_book_completed = True,
            is_story_book_completed = False,
            is_video_completed = False
        )
        db.session.add(progress_db)
        db.session.commit()

    else: 
        progress.is_grammar_book_completed = True
        db.session.commit()

    return redirect(f'/users/{user.id}')
@app.route('/story-book-completed')
def story_book_completed():
    
    user = g.user
    progress = Progress.query.filter_by(user_id = user.id).first()
    if not progress:
        progress_db = Progress(
            user_id = user.id,
            quiz_score = 0,
            is_grammar_book_completed = False,
            is_story_book_completed = True,
            is_video_completed = False
        )
        db.session.add(progress_db)
        db.session.commit()

    else: 
        progress.is_story_book_completed = True
        db.session.commit()

    return redirect(f'/users/{user.id}')

@app.route('/video-completed')
def video_completed():
    
    user = g.user
    progress = Progress.query.filter_by(user_id = user.id).first()
    if not progress:
        progress_db = Progress(
            user_id = user.id,
            quiz_score = 0,
            is_grammar_book_completed = False,
            is_story_book_completed = False,
            is_video_completed = True
        )
        db.session.add(progress_db)
        db.session.commit()

    else: 
        progress.is_video_completed = True
        db.session.commit()

    return redirect(f'/users/{user.id}')
##############################################################################
# Homepage and error pages




@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        # liked_msg_ids2 = []
        # # for msg in g.user.likes:
        # #     liked_msg_ids2.append(msg.id)

        return redirect(f'/users/{g.user.id}')

    else:
        return render_template('home-anon.html')


@app.route('/get-certificate')
def get_certificate():
    
    user = g.user
     

    return render_template('certificate.html',user=user)


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req


# app.run(debug=True)



