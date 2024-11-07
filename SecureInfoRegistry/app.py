from dotenv import load_dotenv
import os

load_dotenv()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
mail = Mail()

app = Flask(__name__)
app.config.from_object('config.Config')
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')
app.config['DEBUG'] = True



db.init_app(app)
mail.init_app(app)

with app.app_context():
    import models
    db.create_all()  # Create tables if they don't exist

from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
