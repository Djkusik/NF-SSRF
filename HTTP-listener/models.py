from datetime import datetime
from server import db

class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    domain = db.Column(db.String(80), nullable=True)

    def __repr__(self):
        return self.name

class Fire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payload = db.Column(db.Text, nullable=False)
    headers = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=False)
    target = db.relationship('Target', backref=db.backref('targets', lazy=True))