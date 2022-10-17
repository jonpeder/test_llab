from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    initials = db.Column(db.String(3))
    notes = db.relationship('Note')
    print_events = db.relationship('Print_events')
    collecting_events = db.relationship('Collecting_events')    

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))    
    
class Print_events(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    eventID = db.Column(db.String(10))
    print_n = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))

class Country_codes (db.Model):
    countryCode = db.Column(db.String(2), primary_key=True)
    country = db.Column(db.String(100))
    Collecting_events = db.relationship('Collecting_events')

class Collecting_methods(db.Model):
    ID = db.Column(db.String(2), primary_key=True)
    samplingProtocol = db.Column(db.String(20))
    Collecting_events = db.relationship('Collecting_events')

class Collecting_events(db.Model):
    eventID = db.Column(db.String(50), primary_key=True)
    countryCode = db.Column(db.String(2), db.ForeignKey('country_codes.countryCode'))
    stateProvince = db.Column(db.String(50))
    county = db.Column(db.String(50))
    strand_id = db.Column(db.String(5))
    municipality = db.Column(db.String(30))
    locality_1 = db.Column(db.String(50))
    locality_2 = db.Column(db.String(50))
    habitat = db.Column(db.String(100))
    decimalLatitude = db.Column(db.Numeric)
    decimalLongitude = db.Column(db.Numeric)
    coordinateUncertaintyInMeters = db.Column(db.Integer)
    samplingProtocol = db.Column(db.String(2), db.ForeignKey('collecting_methods.ID'))
    eventDate_1 = db.Column(db.String)
    eventDate_2 = db.Column(db.String)
    recordedBy = db.Column(db.String(50))
    eventRemarks = db.Column(db.String(100))
    geodeticDatum = db.Column(db.String(5), default='WGS84')
    databased = db.Column(db.DateTime(timezone=True), default=func.now())
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))
    substrateName=db.Column(db.String(50))
    substrateType=db.Column(db.String(50))
    substratePlantPart=db.Column(db.String(50))

class Collectors (db.Model):
    recordedBy = db.Column(db.String(100), primary_key=True)
    recordedByID = db.Column(db.String(100))

class Event_images (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100))
    imageCategory = db.Column(db.String(20))
    comment = db.Column(db.String(500))  
    eventID = db.Column(db.String(50))
    databased = db.Column(db.DateTime(timezone=True), default=func.now())
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))
    