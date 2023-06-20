from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask import g
# from flask_migrate import Migrate


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'


# Use SQLite for simplicity
db = SQLAlchemy(app)
# migrate = Migrate(app, db)


@app.before_request
def before_request_func():
    if not hasattr(g, 'is_first_request'):
        g.is_first_request = True
        db.create_all()  # Create the database tables before the first request
    else:
        g.is_first_request = False


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    results = db.relationship('QuizResult', backref='user', lazy=True)

    def __repr__(self):
        return '<User %r>' % self.name


class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_name = db.Column(db.String(100), nullable=False)
    quiz_topic = db.Column(db.String(100), nullable=False)  # new field
    score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
