from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = 'test2.sqlite3'


def create_app():
    app = Flask(__name__)

    app.secret_key = "barel31"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'Heroku_Database_URL'#f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)


    from .main import app_main, load_questions_from_web
    from .admin import app_admin

    app.register_blueprint(app_main)
    app.register_blueprint(app_admin)

    load_questions_from_web()

    from .models import User
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
