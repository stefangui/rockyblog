from flask import render_template,flash,redirect,session, url_for, request, g
from app.form import LoginForm, EditForm, PostForm
from flask_login import LoginManager,login_required,login_user,logout_user,current_user
from datetime import datetime
from pprint import pprint
from app import app
from app.models import User,Post
from app.config import Config
from flask_login import LoginManager
from flask_openid import OpenID
from app.models import db
import os


lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
oid = OpenID(app, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'tmp'))

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()

#openID装饰器
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route("/user/<nickname>")
@login_required
def user(nickname):
    user = User.query.filter_by(nickname= nickname).first()
    if user == None:
        flash("User" + nickname + " Not Found")
        return redirect(url_for('index'))
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html',user=user, posts=posts)

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)

@app.route('/login', methods = ['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=['nickname','email'])
    return render_template('login.html',title = 'Sign In',form = form,providers = app.config['OPENID_PROVIDERS'])

@oid.after_login
def after_login(resp):
    if resp.email == None or resp.email == "":
        flash("Invaid Login, Please Try Again!")
    pprint(vars(resp))
    user = User.query.filter_by(nickname=resp.nickname).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None:
            nickname = resp.email.split('@')[0]
        user = User(nickname=nickname, email=resp.email, about_me="", last_seen=datetime.utcnow())
        db.session.add(user)
        db.session.commit()
        db.session.add(user.follow(user))
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t follow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are now following ' + nickname + '!')
    return redirect(url_for('user', nickname=nickname))

@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following ' + nickname + '.')
    return redirect(url_for('user', nickname=nickname))

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.errorhandler(404)
def internal_error(error):
    return render_template("400.html"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("500.html"), 500

@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
@app.route("/index/<int:page>",methods=['GET', 'POST'])
@login_required
def index(page=1):
    user = g.user
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, timestamp=datetime.utcnow(), user_id=g.user.id)
        db.session.add(post)
        db.session.commit()
        flash("Your post now live!")
        return redirect(url_for("index"))

    posts = g.user.followed_posts().paginate(page, Config.POSTS_PER_PAGE, False)
    pprint(posts)
    return render_template("index.html",title= "home", user= user, form=form, posts= posts)