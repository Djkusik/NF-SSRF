from flask_sqlalchemy import SQLAlchemy

db = None

def create_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///listeners.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    global db
    db = SQLAlchemy(app)
    from models import Fire, Target
    db.create_all()
    return db