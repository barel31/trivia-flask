import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.

db = SQLAlchemy()
DB_NAME = os.environ['DATABASE_NAME']


def create_app():
    app = Flask(__name__)

    app.secret_key = os.environ['DATABASE_SECRET_KEY']
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URI']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)


    from .main import app_main, load_questions_from_web
    from .admin import app_admin

    app.register_blueprint(app_main)
    app.register_blueprint(app_admin)

    load_questions_from_web()

    from website.models import User
    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
