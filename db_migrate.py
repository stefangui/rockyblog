from app import app,db
from flask_migrate import MigrateCommand,Migrate,Manager

migrate = Migrate(app,db) #app就是你的FLASK，DB为你的SQLALCHEMY连接句柄
manager = Manager(app)
manager.add_command('db',MigrateCommand)
manager.run()