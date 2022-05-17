from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = 'test2.sqlite3'
DB_SECRET = 'barel31'
DB_URI = 'postgresql://zzeoiakyeudtph:6d662bd9771ce97f738b769f29d3100ca8996d41c26bbc3cbec6d4742cd904a2@ec2-35-153-35-94.compute-1.amazonaws.com:5432/d5e7lpuv8v66ck'#f'sqlite:///{DB_NAME}'

def create_app():
    app = Flask(__name__)

    app.secret_key = DB_SECRET
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
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
