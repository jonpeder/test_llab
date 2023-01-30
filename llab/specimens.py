# load packages
from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_required, current_user
import sqlite3
from .models import User, Collectors, Occurrences, Taxa, Identification_events, Collecting_events, Country_codes
from . import db
import re
import datetime
import uuid
import time
import requests
import numpy as np

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
                                specimen = specimen.replace("http://purl.org/nhmuio/id/", "") # Remove NHMO shit
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
                                # If collecting_event exist, create a new occurrence-record if the occurrence-id does not exist:
                                elif Collecting_events.query.filter_by(eventID=specimen.split(";")[0]).first():
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
                                else:
                                    flash(f"Occurrence-ID {specimen} does not exist and does not include a valid event-ID. Occurrence-record was not created.", category="error")
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
@specimens.route('/specimen_get')
@login_required
def specimen_get():
    title = "Get specimen data"
    # Prepare list of taxa for dropdown-select-search bar
    taxa = Taxa.query.all()  # Database query for taxa
    cl = tuple(np.unique([i.cl for i in taxa if i.cl]))
    order = tuple(np.unique([i.order for i in taxa if i.order]))
    family = tuple(np.unique([i.family for i in taxa if i.family]))
    genus = tuple(np.unique([i.genus for i in taxa if i.genus]))
    scientificName = tuple(np.unique([i.scientificName for i in taxa]))
    dropdown_names = cl+order+family+genus+scientificName
    dropdown_ranks = tuple(len(cl)*["class"]+len(order)*["order"]+len(family)*["family"]+len(genus)*[
                           "genus"]+len(scientificName)*["scientificName"])
    return render_template("specimen_get.html", title=title, user=current_user, dropdown_names=dropdown_names, dropdown_ranks=dropdown_ranks)

# Query database for specimen-data and render a specimen-table 
@specimens.route('/specimen_list', methods=["POST", "GET"])
@login_required
def specimen_list():
    title = "Speciemen table"
    order = ['species', 'spnov', 'species-group', 'genus', 'tribe', 'subfamily', 'family', 'superfamily', 'infraorder', 'order', 'class', 'other']
    occurrence_ids=""
    # Get data from specimen_get
    if request.form.get('specimen_find') == 'specimen_find':
        #
        # 1. Event-label QR-code data
        qr_data = request.form.get("occurrence_ids")
        occurrence_ids_1 = qr_data.splitlines()
        occurrence_ids_1 = [i.replace("http://purl.org/nhmuio/id/", "") for i in occurrence_ids_1]
        #
        # 2. Select taxa
        taxa = request.form.getlist("taxon_name")
        # Loop over selected taxa and get scientific names of (children) species
        scientific_names = list()
        for i in taxa:
            taxon = i.split(";")
            # Query occurrences of given taxon
            if (taxon[1] == "scientificName"):
                scientific_names_tmp = [taxon[0]]
            else:
                if (taxon[1] == "class"):
                    taxa_db = Taxa.query.filter_by(cl=taxon[0])
                if (taxon[1] == "order"):
                    taxa_db = Taxa.query.filter_by(order=taxon[0])
                if (taxon[1] == "family"):
                    taxa_db = Taxa.query.filter_by(family=taxon[0])
                if (taxon[1] == "genus"):
                    taxa_db = Taxa.query.filter_by(genus=taxon[0])
                scientific_names_tmp = [i.scientificName for i in taxa_db if i.scientificName]
            scientific_names = scientific_names+list(scientific_names_tmp)
        scientific_names = np.unique(scientific_names)
        # Get occurrences for selected taxa
        #occurrences_db = Occurrences.query.filter(Occurrences.scientificName.in_(scientific_names)).all()
        occurrences_db = Occurrences.query\
            .join(Identification_events, Occurrences.identificationID==Identification_events.identificationID)\
            .with_entities(Occurrences.occurrenceID, Identification_events.scientificName)\
            .filter(Identification_events.scientificName.in_(scientific_names))\
            .all()
        occurrence_ids_2 = [i.occurrenceID for i in occurrences_db if i.occurrenceID]
        ## 3. Unit qr-codes
        unit_ids = request.form.get("unit_ids")
        unit_ids = unit_ids.splitlines()
        unit_ids = [i.split(";")[3] for i in unit_ids]
        occurrences_db = Occurrences.query.filter(Occurrences.unit_id.in_(unit_ids))
        occurrence_ids_3 = [i.occurrenceID for i in occurrences_db]
        ## Concateneate occurrence-ID lists from the differnt sources
        occurrence_ids = np.unique(occurrence_ids_1 + occurrence_ids_2 + occurrence_ids_3)
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
            .with_entities(Occurrences.occurrenceID, Country_codes.country, Collecting_events.eventID, 
            Collecting_events.municipality, Collecting_events.locality_1, Collecting_events.locality_2, 
            Collecting_events.habitat, Collecting_events.substrateName, Collecting_events.substratePlantPart, 
            Collecting_events.substrateType, Collecting_events.eventDate_1, Collecting_events.eventDate_2, 
            Collecting_events.samplingProtocol, Collecting_events.recordedBy, Taxa.scientificName, Taxa.family, 
            Taxa.order, Taxa.taxonRank, Taxa.scientificNameAuthorship, Identification_events.identifiedBy, 
            Identification_events.dateIdentified, Identification_events.identificationQualifier, Identification_events.sex)\
            .order_by(Taxa.scientificName, Collecting_events.eventID)\
            .all()
    # Report if any of the specified occurrenceIDs are not present in database.
    for occurrence in occurrence_ids:
        if occurrence not in [i.occurrenceID for i in occurrences]:
            flash(f'{occurrence} not in database', category="error")
    # Return template
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
        .order_by(Identification_events.dateIdentified.desc())\
        .all()
    return render_template("specimen_view.html", title=title, user=current_user, occurrence=occurrence, identifications=identifications)

# Get specimen data from GBIF
@specimens.route('/specimen_gbif', methods=['GET', 'POST'])
@login_required
def specimen_gbif():
    title = "Add specimen from GBIF"
    # Function to return value from dictionary or empty value if the value does not exist
    def if_exists(name, dict_name):
        if name in dict_name:
            return dict_name[name]
        else:
            return ""
    # Post request
    if request.method == 'POST':
        occurrence_ids = request.form.get("occurrence_ids")
        occurrence_ids = occurrence_ids.splitlines()
        # Loop through list of occurrence IDs
        for occurrence_id in occurrence_ids:
            # Prepare URL
            url = f'https://api.gbif.org/v1/occurrence/search?q={occurrence_id}'
            # Make API call
            response = requests.get(url)
            # Get records in results
            all = response.json()["results"]
            # Loop over each record and try to match occurrence_id
            first = ""
            for i in all:
                if "materialSampleID" in i:
                    if i["materialSampleID"] == occurrence_id:
                        first = i
                        occurrence_id = occurrence_id.replace("http://purl.org/nhmuio/id/", "")
            if first:
                # Add Collecting event to database
                if "eventID" in first:
                    event_id = first["eventID"]
                else:
                    event_id = f'NHMO_{if_exists("decimalLatitude", first)}{if_exists("decimalLongitude", first)}{if_exists("eventDate", first)[0:10]}{if_exists("habitat", first)}'
                # New event
                if not Collecting_events.query.filter_by(eventID=event_id).first():
                    new_event = Collecting_events(eventID=event_id, countryCode=if_exists("countryCode", first), 
                        stateProvince=if_exists("stateProvince", first), county=if_exists("county", first), 
                        municipality=if_exists("municipality", first), locality_1=if_exists("locality", first), 
                        habitat=if_exists("habitat", first), decimalLatitude=if_exists("decimalLatitude", first), 
                        decimalLongitude=if_exists("decimalLongitude", first), coordinateUncertaintyInMeters=if_exists("coordinateUncertaintyInMeters", first), 
                        samplingProtocol=if_exists("samplingProtocol", first), eventDate_1=if_exists("eventDate", first)[0:10], recordedBy=if_exists("recordedBy", first).replace(",", "|"), 
                        eventRemarks=if_exists("eventRemarks", first), createdByUserID=current_user.id)
                    # Add new objects to database
                    db.session.add(new_event)
                    # Commit
                    db.session.commit()
                # Add new identification record
                if not Occurrences.query.filter_by(occurrenceID=occurrence_id).first():
                    new_identification=Identification_events(
                                        occurrenceID=occurrence_id,
                                        scientificName="Pteromalidae",
                                        identifiedBy="Jon Peder Lindemann",
                                        lifeStage="adult",
                                        createdByUserID=current_user.id)
                    # Add new objects to database
                    db.session.add(new_identification)
                    # Commit
                    db.session.commit()
                    # Get event-ID
                    db.session.refresh(new_identification)
                    # new occurrence
                    new_occurrence=Occurrences(
                        occurrenceID = occurrence_id,
                        catalogNumber = if_exists("catalogNumber", first),
                        eventID = event_id,
                        identificationID = new_identification.identificationID,
                        ownerInstitutionCode = "NHMO",
                        individualCount = if_exists("individualCount", first),
                        preparations = if_exists("preparations", first),
                        occurrenceRemarks = if_exists("occurrenceRemarks", first),
                        createdByUserID = current_user.id
                    )
                    db.session.add(new_occurrence)
                    db.session.commit()
            time.sleep(1)
    return render_template("specimen_gbif.html", title=title, user=current_user)