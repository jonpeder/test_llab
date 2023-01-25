# load packages
from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_required, current_user
import sqlite3
from .models import User, Collectors, Occurrences, Taxa, Identification_events, Collecting_events, Country_codes
from . import db
import re
import datetime

# connect to __init__ file
specimens = Blueprint('specimens', __name__)

# Add determinations to database. Add specimens to database if not already present.
@specimens.route('/specimen_det', methods=["POST", "GET"])
@login_required
def specimen_det():
    title = "New determinations"
    entomologists = Collectors.query.all()
    # Count
    occ_count=0
    occ_update_count=0
    id_count=0
    # POST
    if request.method == 'POST':
        # Mandatory fields
        qr_data = request.form.get("qr_data")
        identifiedBy = request.form.get("identifiedBy")
        ownerInstitutionCode = request.form.get("ownerInstitutionCode")
        sex_tmp = request.form.get("sex")
        lifeStage = request.form.get("lifeStage")
        individualCount = request.form.get("individualCount")
        preparations = request.form.get("preparations")
        identificationQualifier_tmp = request.form.get("identificationQualifier")
        # Optional fields
        identificationRemarks = request.form.get("identificationRemarks")
        occurrenceRemarks = request.form.get("occurrenceRemarks")
        associatedTaxa = request.form.get("associatedTaxa")
        associatedReferences = request.form.get("associatedReferences")
        verbatimLabel = request.form.get("verbatimLabel")
        # Check that a det label have been scanned, that  ".det" is present in string
        if re.search("det\.", qr_data):
            # For each taxon
            for det in qr_data.split("det."):
                # Check that the variable is not empty
                if det:
                    # get det-data
                    det_data = det.splitlines()[0]
                    # get scientific name
                    scientificName = det_data.split(";")[0]
                    # Get identification-qualifier and sex
                    if det_data.split(";")[1]:
                        identificationQualifier = det_data.split(";")[1]
                    else:
                        identificationQualifier = identificationQualifier_tmp
                    if det_data.split(";")[2]:
                        sex = det_data.split(";")[2]
                    else:
                        sex = sex_tmp
                    # Get unit-ID
                    unit_id = det_data.split(";")[3]
                    # Check that the taxon exists in Taxa-table
                    if Taxa.query.filter_by(scientificName=scientificName).first():
                        # Check that a specimen have been scanned after the taxon
                        if len(det.splitlines()) > 1:
                            # For each specimen identified to the current taxon, add record to database (populate Occurrences)
                            for specimen in det.splitlines()[1:]:
                                # Function for creating a new identification-event-record
                                def new_id():
                                    new_identification=Identification_events(
                                        occurrenceID=specimen,
                                        scientificName=scientificName,
                                        identificationQualifier=identificationQualifier,
                                        identifiedBy=identifiedBy,
                                        sex=sex,
                                        lifeStage=lifeStage,
                                        identificationRemarks=identificationRemarks,
                                        createdByUserID=current_user.id
                                    )
                                    return new_identification
                                # If the occurrence-id exist, update the occurrence record:
                                if Occurrences.query.filter_by(occurrenceID=specimen).first():
                                    #flash(f'{specimen} exists')
                                    occurrence = Occurrences.query.filter_by(occurrenceID=specimen).first()
                                    identification = Identification_events.query.filter_by(identificationID=occurrence.identificationID).first()
                                    # If identification-event does not exist or if the scientific name has been changed, 
                                    # create a new identification-event-record and update Occurrence-record
                                    if occurrence.identificationID == "" or identification.scientificName != scientificName:
                                        new_identification = new_id()
                                        db.session.add(new_identification)
                                        # Commit new identification
                                        id_count+=1
                                        db.session.commit()
                                        db.session.refresh(new_identification)
                                        occurrence.identificationID = new_identification.identificationID
                                        occurrence.unit_id = unit_id
                                    # If Identification_event exists and the scientific name is the same as before, update Occurrence
                                    else:
                                        occurrence.unit_id = unit_id
                                    # Commit 
                                    occ_update_count+=1
                                    db.session.commit()
                                # Create a new occurrence-record if the occurrence-id does not exist:
                                else:
                                    # First create the Identification-record
                                    new_identification = new_id()
                                    db.session.add(new_identification)
                                    # Commit new identification
                                    id_count+=1
                                    db.session.commit()
                                    db.session.refresh(new_identification)
                                    # Then the Occurrence-record
                                    new_occurrence=Occurrences(
                                        occurrenceID = specimen,
                                        eventID = specimen.split(";")[0],
                                        identificationID = new_identification.identificationID,
                                        ownerInstitutionCode = ownerInstitutionCode,
                                        individualCount = individualCount,
                                        preparations = preparations,
                                        occurrenceRemarks = occurrenceRemarks,
                                        associatedTaxa = associatedTaxa,
                                        associatedReferences = associatedReferences,
                                        verbatimLabel = verbatimLabel,
                                        unit_id = unit_id,
                                        createdByUserID = current_user.id
                                    )
                                    db.session.add(new_occurrence)
                                    # Commit
                                    occ_count+=1
                                    db.session.commit()
                            if occ_count > 0:
                                flash(f'Occurrences added: {occ_count}')
                            if occ_update_count > 0:
                                flash(f'Occurrences updated: {occ_update_count}')
                            if id_count > 0:
                                flash(f'Identifications added: {id_count}')
                        else:
                            flash(f'No specimen scanned after {scientificName}', category="error")
                    else:
                        flash(
                            f'{scientificName} does not exist in database', category="error")
        else:
            flash("A determination should be inserted!", category="error")
    # Return html-page
    return render_template("specimen_det.html", title=title, user=current_user, entomologists=entomologists)


# Send decoded qr-codes from specimen-labels to get specimen table
@specimens.route('/specimen_find')
@login_required
def specimen_find():
    title = "Find specimen data"
    return render_template("specimen_find.html", title=title, user=current_user)

# Query database for specimen-data and render a specimen-table 
@specimens.route('/specimen_list', methods=["POST", "GET"])
@login_required
def specimen_list():
    title = "Speciemen table"
    order = ['species', 'spnov', 'species-group', 'genus', 'tribe', 'subfamily', 'family', 'superfamily', 'infraorder', 'order', 'class', 'other']
    occurrence_ids=""
    # If requested, get occurrence ids from decoded qr_specimen_labels
    if request.form.get('qr_specimen_labels') == 'qr_specimen_labels':
        qr_data = request.form.get("qr_data")
        occurrence_ids = qr_data.splitlines()
    # If requested, get event-id from show_event.html
    if request.form.get("collecting_event_id") == "collecting_event_id":
        eventID = request.form.get("eventID")
        event = Collecting_events.query.filter_by(eventID=eventID).first()
        occurrence_ids = [i.occurrenceID for i in event.occurrences]
    # Make database query
    occurrences = Occurrences.query.filter(Occurrences.occurrenceID.in_(occurrence_ids))\
            .join(Identification_events, Occurrences.identificationID==Identification_events.identificationID)\
            .join(Taxa, Identification_events.scientificName==Taxa.scientificName)\
            .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
            .join(Country_codes, Collecting_events.countryCode==Country_codes.countryCode)\
            .with_entities(Occurrences.occurrenceID, Country_codes.country, Collecting_events.eventID, Collecting_events.municipality, Collecting_events.locality_1, Collecting_events.locality_2, Collecting_events.habitat, Collecting_events.substrateName, Collecting_events.substratePlantPart, Collecting_events.substrateType, Collecting_events.eventDate_1, Collecting_events.eventDate_2, Collecting_events.samplingProtocol, Collecting_events.recordedBy, Taxa.scientificName, Taxa.family, Taxa.order, Taxa.taxonRank, Taxa.scientificNameAuthorship, Identification_events.identifiedBy, Identification_events.dateIdentified, Identification_events.identificationQualifier, Identification_events.sex)\
            .order_by(Taxa.scientificName, Collecting_events.eventID)\
            .all()
    return render_template("specimen_list.html", title=title, user=current_user, occurrences=occurrences, order=order)

# Query database for specimen-data and render a specimen-table 
@specimens.route('/specimen_view/<string:occurrence_id>/', methods=['GET'])
@login_required
def specimen_view(occurrence_id):
    title = "Specimen page"
    # Query Occurrence data
    occurrence = Occurrences.query.filter_by(occurrenceID=occurrence_id)\
            .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
            .join(Country_codes, Collecting_events.countryCode==Country_codes.countryCode)\
            .with_entities(Occurrences.occurrenceID, Occurrences.identificationID, Occurrences.catalogNumber, Occurrences.individualCount, 
            Occurrences.preparations, Occurrences.occurrenceRemarks, Occurrences.associatedTaxa, 
            Occurrences.associatedReferences, Occurrences.ownerInstitutionCode, Occurrences.verbatimLabel,
            Country_codes.country, Collecting_events.eventID, Collecting_events.municipality,
            Collecting_events.locality_1, Collecting_events.locality_2, Collecting_events.habitat, Collecting_events.substrateName, 
            Collecting_events.substratePlantPart, Collecting_events.substrateType, Collecting_events.eventDate_1, 
            Collecting_events.eventDate_2, Collecting_events.samplingProtocol, Collecting_events.recordedBy, Collecting_events.decimalLatitude, 
            Collecting_events.decimalLongitude, Collecting_events.coordinateUncertaintyInMeters, Collecting_events.eventRemarks)\
            .first()
    # Query identification events
    identifications = Identification_events.query.filter_by(occurrenceID=occurrence_id)\
        .join(Taxa, Identification_events.scientificName==Taxa.scientificName)\
        .with_entities(Taxa.scientificName, Taxa.scientificNameAuthorship, Taxa.specificEpithet, Taxa.taxonID, 
        Taxa.taxonRank, Taxa.genus, Taxa.family, Taxa.order, Taxa.cl, Identification_events.identificationID,
        Identification_events.identificationQualifier, Identification_events.sex, Identification_events.lifeStage, 
        Identification_events.identifiedBy, Identification_events.dateIdentified, Identification_events.identificationRemarks)\
        .all()
    return render_template("specimen_view.html", title=title, user=current_user, occurrence=occurrence, identifications=identifications)
