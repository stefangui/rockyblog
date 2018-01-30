from flask import render_template,flash,redirect,session, url_for, request, g
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_openid import OpenID
import config
from hashlib import md5
import os

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
oid = OpenID(app, os.path.join(config.basedir, 'tmp'))


followers = db.Table("followers",
         db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
         db.Column("followed_id", db.Integer, db.ForeignKey("user.id"))
)

class User(db.Model):
    global followers
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    followed = db.relationship("User",
           secondary = followers,
           primaryjoin = (followers.c.follower_id == id),
           secondaryjoin = (followers.c.followed_id == id),
           backref = db.backref("followers", lazy = 'dynamic'),
           lazy = 'dynamic'
    )

    is_authenticated = True
    is_active = True
    is_anonymous = False

    def get_id(self):
        return str(self.id)  # python 3
    def avatar(self, size):
        return 'http://www.gravatar.com/avatar/' + get_md5(self.email.encode("utf-8")) + '?d=mm&s=' + str(size)
    def __repr__(self):
        return '<User %r>' % (self.nickname)
    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() == None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname=new_nickname).first() == None:
                break
            version += 1
        return new_nickname
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self
    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0
    def followed_posts(self):
        return Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(
            followers.c.follower_id == self.id).order_by(Post.timestamp.desc())


class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post %r>' % (self.body)


def get_md5(url):
    m = md5()
    m.update(url)
    return m.hexdigest()


