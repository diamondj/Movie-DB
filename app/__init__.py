import os
import MySQLdb 

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@127.0.0.1:3306/moviedb'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moviedb.db'




db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

basedir = os.path.abspath(os.path.dirname(__file__))

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from app import models, views



