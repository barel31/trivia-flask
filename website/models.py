from website import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = 'users' # old database table name
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    score = db.Column(db.Integer)

    def __init__(self, name, score=0):
        self.name = name
        self.score = score
