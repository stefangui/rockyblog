from app import app,db
from app.models import User

u = User(nickname='john2', email='john2@email.com')
u = User(nickname='susan1', email='susan1@email.com')
u = User(nickname='susan2', email='susan2@email.com')
u = User(nickname='susan3', email='susan3@email.com')
u = User(nickname='susan4', email='susan4@email.com')
u = User(nickname='susan5', email='susan5@email.com')
db.session.add(u)
db.session.commit()