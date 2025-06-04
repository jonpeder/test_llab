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
    decimalLatitude = db.Column(db.Numeric(11,8))
    decimalLongitude = db.Column(db.Numeric(11,8))
    coordinateUncertaintyInMeters = db.Column(db.Integer)
    samplingProtocol = db.Column(db.String(20))
    eventDate_1 = db.Column(db.String(10))
    eventDate_2 = db.Column(db.String(10))
    recordedBy = db.Column(db.String(50))
    eventRemarks = db.Column(db.String(100))
    geodeticDatum = db.Column(db.String(5), default='WGS84')
    databased = db.Column(db.DateTime(timezone=True), default=func.now())
    createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))
    substrateName = db.Column(db.String(50))
    substrateType = db.Column(db.String(50))
    substratePlantPart = db.Column(db.String(50))
    occurrences = db.relationship('Occurrences')
    eunisCode = db.Column(db.String(5))

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
    createdByUserID = db.Column(db.Integer, db.ForeignKey('user.id'))

class Drawers (db.Model):
    drawerName = db.Column(db.String(25), primary_key=True)
    databased = db.Column(db.DateTime(timezone=True), default=func.now())
    createdByUserID = db.Column(db.Integer, db.ForeignKey('user.id'))

class Units (db.Model):
    unitID = db.Column(db.String(80), primary_key=True)
    drawerName = db.Column(db.String(25), db.ForeignKey('drawers.drawerName'))
    taxonInt = db.Column(db.Integer)
    identificationQualifier = db.Column(db.String(10))
    sex = db.Column(db.String(6))
    databased = db.Column(db.DateTime(timezone=True), default=func.now())
    updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    createdByUserID = db.Column(db.Integer, db.ForeignKey('user.id'))


class Taxa (db.Model):
    taxonInt = db.Column(db.Integer, primary_key=True)
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
    createdByUserID = db.Column(db.Integer, db.ForeignKey('user.id'))
    publishedIn = db.Column(db.String(300))

class Occurrence_images (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    imageCategory = db.Column(db.String(20))
    comment = db.Column(db.String(500))
    occurrenceID = db.Column(db.String(80), db.ForeignKey('occurrences.occurrenceID'))
    databased = db.Column(db.DateTime(timezone=True), default=func.now())
    createdByUserID = db.Column(db.Integer, db.ForeignKey('user.id'))

class Identification_events (db.Model):
    identificationID = db.Column(db.Integer, primary_key=True)
    occurrenceID = db.Column(db.String(80), db.ForeignKey('occurrences.occurrenceID'))
    scientificName = db.Column(db.String(100), db.ForeignKey('taxa.scientificName'))
    identificationQualifier = db.Column(db.String(10))
    identifiedBy = db.Column(db.String(100), db.ForeignKey('collectors.recordedBy'))
    sex = db.Column(db.String(6))
    lifeStage = db.Column(db.String(5))
    identificationRemarks = db.Column(db.String(100))
    dateIdentified = db.Column(db.String(10), default=str(date.today()))
    createdByUserID = db.Column(db.Integer, db.ForeignKey('user.id'))

class Catalog_number_counter(db.Model):
    id = db.Column(db.Integer, primary_key=True)

class Unit_id_counter(db.Model):
    id = db.Column(db.Integer, primary_key=True)

class Illustrations (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    imageType = db.Column(db.String(20))
    category = db.Column(db.String(20))
    scientificName = db.Column(db.String(50))
    sex = db.Column(db.String(6))
    lifeStage = db.Column(db.String(5))
    identificationQualifier = db.Column(db.String(10))
    identifiedBy = db.Column(db.String(100))
    typeStatus = db.Column(db.String(100))
    ownerInstitutionCode = db.Column(db.String(100))
    rightsHolder = db.Column(db.String(100))
    license = db.Column(db.String(100))
    associatedReference = db.Column(db.String(100))
    remarks = db.Column(db.String(500))
    createdByUserID = db.Column(db.Integer, db.ForeignKey('user.id'))
    typeID = db.Column(db.String(255))
    scaleBar = db.Column(db.String(50))
    typeName = db.Column(db.String(100))
    databased = db.Column(db.DateTime(timezone=True), default=func.now())

class Datasets(db.Model):
    datasetName = db.Column(db.String(100), primary_key=True)
    datasetDescription = db.Column(db.String)
    specimenIDs = db.Column(db.String)
    datasetManager = db.Column(db.String)
    rightsHolder = db.Column(db.String)
    license = db.Column(db.String)
    createdByUserID = db.Column(db.Integer, db.ForeignKey('user.id'))
    databased = db.Column(db.DateTime(timezone=True), default=func.now())

class Landmark_datasets(db.Model):
    datasetName = db.Column(db.String(100), primary_key=True)
    landmarks = db.Column(db.String)
    taxa = db.Column(db.String)
    imageCategory = db.Column(db.String)
    imageIDs = db.Column(db.String)
    createdByUserID = db.Column(db.Integer, db.ForeignKey('user.id'))
    databased = db.Column(db.DateTime(timezone=True), default=func.now())


class Landmarks(db.Model):
    landmark = db.Column(db.String(10), primary_key=True)
    filename = db.Column(db.Integer, primary_key=True)
    datasetName = db.Column(db.String(100), primary_key=True)
    xCoordinate = db.Column(db.Numeric)
    yCoordinate = db.Column(db.Numeric)
    createdByUserID = db.Column(db.Integer, db.ForeignKey('user.id'))
    databased = db.Column(db.DateTime(timezone=True), default=func.now())

class Eunis_habitats(db.Model):
    eunisCode = db.Column(db.String(5), primary_key=True)
    level2 = db.Column(db.String(5))
    level1 = db.Column(db.String(5))
    redlistCode = db.Column(db.String(10))
    habitatName = db.Column(db.String(200))

class Observations(db.Model):
    occurrenceID = db.Column(db.String, primary_key=True)
    taxonInt = db.Column(db.Integer)
    imageFileNames = db.Column(db.String)
    eventDateTime = db.Column(db.String(19))
    decimalLatitude = db.Column(db.Numeric(11,8))
    decimalLongitude = db.Column(db.Numeric(11,8))
    coordinateUncertaintyInMeters = db.Column(db.Integer)
    countryCode = db.Column(db.String(2))
    county = db.Column(db.String)
    municipality = db.Column(db.String)
    locality = db.Column(db.String)
    individualCount = db.Column(db.Integer)
    lifeStage = db.Column(db.String)
    sex = db.Column(db.String)
    recordedBy = db.Column(db.String)
    occurrenceRemarks = db.Column(db.String)
    createdByUserID = db.Column(db.Integer, db.ForeignKey('user.id'))
    databased = db.Column(db.DateTime(timezone=True), default=func.now())
    identifiedBy = db.Column(db.String(100), db.ForeignKey('collectors.recordedBy'))
    dateIdentified = db.Column(db.String(10), default=str(date.today()))

# Pteromalidae database
class Pteromalidae_norway(db.Model):
    occurrenceID = db.Column(db.String(100), primary_key=True)
    eventID = db.Column(db.String(100))
    scientificName = db.Column(db.String(100))
    notes = db.Column(db.String(255))
    reference = db.Column(db.String(255))
    institutionCode = db.Column(db.String(20))
    source = db.Column(db.String(20))
    sex = db.Column(db.String(10))
    individualCount = db.Column(db.Integer)
    identifiedBy = db.Column(db.String(200))
    county = db.Column(db.String(255))
    strand = db.Column(db.String(255))
    municipality = db.Column(db.String(255))
    locality = db.Column(db.String(255))
    habitat = db.Column(db.String(255))
    decimalLatitude = db.Column(db.Numeric(11,8))
    decimalLongitude = db.Column(db.Numeric(11,8))
    coordinateUncertaintyInMeters = db.Column(db.Integer)
    samplingProtocol = db.Column(db.String(100))
    eventDate_1 = db.Column(db.String(10))
    eventDate_2 = db.Column(db.String(10))
    recordedBy = db.Column(db.String(255))
    catalogNumber = db.Column(db.String(100))
    basisOfRecord = db.Column(db.String(100))
    dataset = db.Column(db.String(255))
    occurrenceRemarks = db.Column(db.String)
    eventRemarks = db.Column(db.String)
    
class Chalcidoidea(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    parent = db.Column(db.Integer)
    name = db.Column(db.String(100))
    author = db.Column(db.String(100))
    rank = db.Column(db.String(100))
    family = db.Column(db.String(100))
    subfamily = db.Column(db.String(100))
    tribe = db.Column(db.String(100))
    status = db.Column(db.String(10))
    extant = db.Column(db.String(10))

class co1(db.Model):
    sequenceID = db.Column(db.String(100), primary_key=True)
    occurrenceID = db.Column(db.String(100))
    sequence = db.Column(db.String)
    sequence_length = db.Column(db.Integer)
    source = db.Column(db.String(50))

class Sequence_alignment(db.Model):
    sequenceID = db.Column(db.String(100), primary_key=True)
    sequence = db.Column(db.String)
    createdByUserID = db.Column(db.Integer, db.ForeignKey('user.id'))