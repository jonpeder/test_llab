from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import date

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    initials = db.Column(db.String(3))
    entomologist_name = db.Column(db.String(100), db.ForeignKey('Collectors.recordedBy'))
    institutionCode = db.Column(db.String(20))
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))
    print_events = db.relationship('Print_events')
    print_det = db.relationship('Print_det')
    collecting_events = db.relationship('Collecting_events')
    occurrences = db.relationship('Occurrences')
    collectors = db.relationship('Collectors')
    taxa = db.relationship('Taxa')

class Print_events(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventID = db.Column(db.String(10))
    print_n = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))

class Print_det(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scientificName = db.Column(db.String(100))
    identificationQualifier = db.Column(db.String(10))
    sex = db.Column(db.String(6))
    print_n = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))
    
class Country_codes (db.Model):
    countryCode = db.Column(db.String(2), primary_key=True)
    country = db.Column(db.String(100))
    Collecting_events = db.relationship('Collecting_events')

class Collecting_events(db.Model):
    eventID = db.Column(db.String(50), primary_key=True)
    countryCode = db.Column(
        db.String(2), db.ForeignKey('country_codes.countryCode'))
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
    samplingProtocol = db.Column(db.String(20))
    eventDate_1 = db.Column(db.String)
    eventDate_2 = db.Column(db.String)
    recordedBy = db.Column(db.String(50))
    eventRemarks = db.Column(db.String(100))
    geodeticDatum = db.Column(db.String(5), default='WGS84')
    databased = db.Column(db.DateTime(timezone=True), default=func.now())
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))
    substrateName = db.Column(db.String(50))
    substrateType = db.Column(db.String(50))
    substratePlantPart = db.Column(db.String(50))

class Collectors (db.Model):
    recordedBy = db.Column(db.String(100), primary_key=True)
    recordedByID = db.Column(db.String(100))
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))

class Event_images (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100))
    imageCategory = db.Column(db.String(20))
    comment = db.Column(db.String(500))
    eventID = db.Column(db.String(50))
    databased = db.Column(db.DateTime(timezone=True), default=func.now())
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))

class Occurrences (db.Model):
    occurrenceID = db.Column(db.String(80), primary_key=True)
    eventID = db.Column(db.String(20), db.ForeignKey(
        'collecting_events.eventID'))
    identificationID = db.Column(db.Integer, db.ForeignKey('identification_events.identificationID'))
    individualCount = db.Column(db.Integer)
    preparations = db.Column(db.String(50))
    occurrenceRemarks = db.Column(db.String(100))
    associatedTaxa = db.Column(db.String(100))
    associatedReferences = db.Column(db.String(100))
    unit_id = db.Column(db.String(80))
    ownerInstitutionCode = db.Column(db.String(20))
    databased = db.Column(db.DateTime(timezone=True), default=func.now())
    modified = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    last_export = db.Column(db.DateTime)
    catalogNumber = db.Column(db.String(20))
    verbatimLabel = db.Column(db.String(250))
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))

class Taxa (db.Model):
    scientificName = db.Column(db.String(100), primary_key=True)
    taxonRank = db.Column(db.String(50))
    scientificNameAuthorship = db.Column(db.String(50))
    specificEpithet = db.Column(db.String(50))
    genus = db.Column(db.String(50))
    family = db.Column(db.String(50))
    order = db.Column(db.String(50))
    kingdom = db.Column(db.String(50), default="Animalia")
    phylum = db.Column(db.String(50), default="Arthropoda")
    cl = db.Column("class", db.String(50))
    nomenclaturalCode = db.Column(db.String(10), default="ICZN")
    taxonID = db.Column(db.String(100))
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))
    publishedIn = db.Column(db.String(300))

class Occurrence_images (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    imageCategory = db.Column(db.String(20))
    comment = db.Column(db.String(500))
    occurrenceID = db.Column(db.String(50), db.ForeignKey('occurrences.occurrenceID'))
    databased = db.Column(db.DateTime(timezone=True), default=func.now())
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))

class Identification_events (db.Model):
    identificationID = db.Column(db.Integer, primary_key=True)
    occurrenceID = db.Column(db.String(80), db.ForeignKey('occurrences.occurrenceID'))
    scientificName = db.Column(db.String(100), db.ForeignKey('taxa.scientificName'))
    identificationQualifier = db.Column(db.String(10))
    identifiedBy = db.Column(db.String(100), db.ForeignKey('collectors.recordedBy'))
    sex = db.Column(db.String(6))
    lifeStage = db.Column(db.String(5))
    identificationRemarks = db.Column(db.String(100))
    dateIdentified = db.Column(db.String, default=str(date.today()))
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))


#insert into Identification_events (scientificName, occurrenceID, identifiedBy, sex, lifeStage, dateIdentified) select scientificName, occurrenceID, identifiedBy, sex, lifeStage, dateIdentified from Occurrences;

"""
CREATE TABLE Occurrences2 (
            occurrenceID VARCHAR (80) NOT NULL,
            eventID VARCHAR (20),
            identificationID INT,
            individualCount INT,
            lifeStage VARCHAR (5), 
            preparations VARCHAR (50),
            occurrenceRemarks VARCHAR (100),
            associatedTaxa VARCHAR (100),
            associatedReferences VARCHAR (100),
            unit_id VARCHAR (80),
            ownerInstitutionCode VARCHAR (20),
            databased TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_export TIMESTAMP, 
            catalogNumber VARCHAR (20), 
            verbatimLabel VARCHAR(250), 
            createdByUserID INT, 
            PRIMARY KEY (occurrenceID),
            FOREIGN KEY (eventID)
                  REFERENCES Collecting_events (eventID) ON UPDATE RESTRICT ON DELETE CASCADE,
            FOREIGN KEY (identificationID)
                  REFERENCES Identification_events(identificationID),
            FOREIGN KEY (createdByUserID)
                  REFERENCES user(createdByUserID)
            );
insert into Occurrences2 (occurrenceID,eventID,identificationID,individualCount,lifeStage,preparations,occurrenceRemarks,associatedTaxa,associatedReferences,unit_id,ownerInstitutionCode,databased,modified,last_export,catalogNumber,verbatimLabel,createdByUserID) select occurrenceID,eventID,identificationID,individualCount,lifeStage,preparations,occurrenceRemarks,associatedTaxa,associatedReferences,unit_id,ownerInstitutionCode,databased,modified,last_export,catalogNumber,verbatimLabel,createdByUserID from Occurrences;

CREATE TABLE Collecting_methods (
           ID CHAR (2) NOT NULL,
           samplingProtocol VARCHAR (20),
           PRIMARY KEY (ID)
           );

sn|Sweep-net
mt|Malaise-trap
wt|Window-trap
pt|Pan-trap
yp|Yellow pan
wp|White pan
bp|Blue pan
it|Intercept-trap
st|Slam-trap
hp|Hand-picked
rd|Reared
lt|Light-trap
pf|Pitfall-trap
"""