from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref

db = SQLAlchemy()

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id', ondelete="CASCADE"))

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sent_documents = db.Column(db.JSON, nullable=True)
    contracts = db.relationship('Contract', backref=backref('contract', uselist=False), lazy=True)
    netrika_id = db.Column(db.String(255), nullable=True)