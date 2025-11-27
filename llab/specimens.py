# load packages
from .functions import bar_plot_dict
from flask import Blueprint, request, redirect, url_for, render_template, flash, request, jsonify
from flask_login import login_required, current_user
import sqlite3
from .models import User, Collectors, Occurrences, Taxa, Identification_events, Collecting_events, Country_codes, Eunis_habitats, Datasets, Units, co1
from . import db
import re
import datetime
import uuid
import time
import requests
import numpy as np
import pandas as pd

# connect to __init__ file
specimens = Blueprint('specimens', __name__)

# Add determinations to database. Add specimens to database if not already present.
@specimens.route('/specimen_det', methods=["POST", "GET"])
@login_required
def specimen_det():
    title = "Add identifications"
    entomologists = Collectors.query.all()
    # If decoded_QR_codes is not specified
    decoded_QR_codes = ""
    # Count
    occ_count=0
    occ_update_count=0
    id_count=0
    # Søk etter Taxa
    taxa = Taxa.query.all()
    # POST
    if request.method == 'POST':
        # Mandatory fields
        qr_data = request.form.get("qr_data")
        taxonInt = request.form.get("taxonInt")
        identifiedBy = request.form.get("identifiedBy")
        individualCount = request.form.get("individualCount")
        preparations = request.form.get("preparations")
        identificationQualifier_tmp = request.form.get("identificationQualifier")
        sex_tmp = request.form.get("sex")
        lifeStage = request.form.get("lifeStage")
        # Optional fields
        identificationRemarks = request.form.get("identificationRemarks")
        occurrenceRemarks = request.form.get("occurrenceRemarks")
        associatedTaxa = request.form.get("associatedTaxa")
        associatedReferences = request.form.get("associatedReferences")
        verbatimLabel = request.form.get("verbatimLabel")
        # If no "TAX:" prefix is present in the string use taxonID if this has been specified
        if not re.search("TAX\:", qr_data):
            if taxonInt:
                qr_data = "TAX:"+taxonInt+":::\n" + qr_data

        # Check that a det label have been scanned, that  "TAX:" is present in string
        if re.search("TAX\:", qr_data):
            # For each taxon
            for det in qr_data.split("TAX:"):
                # Check that the variable is not empty
                if det:
                    # get det-data
                    det_data = det.splitlines()[0]
                    # get scientific name-ID
                    taxonInt = det_data.split(":")[0]
                    # Get identification-qualifier and sex
                    if det_data.split(":")[1]:
                        identificationQualifier = det_data.split(":")[1]
                    else:
                        identificationQualifier = identificationQualifier_tmp
                    if det_data.split(":")[2]:
                        sex = det_data.split(":")[2]
                        if sex == "m":
                            sex = "male"
                        else:
                            sex = "female"
                    else:
                        sex = sex_tmp
                    # Get unit-ID. Add to database if not already present
                    if det_data.split(":")[3]:
                        unit_id = f"TAX:{det_data}"
                        if not Units.query.filter_by(unitID=unit_id).first():
                            new_unit = Units(unitID=unit_id, createdByUserID=current_user.id, taxonInt=taxonInt, identificationQualifier=identificationQualifier, sex=sex)
                            db.session.add(new_unit)
                            db.session.commit()
                    else:
                        unit_id = ""
                    # Check that the taxon exists in Taxa-table
                    taxon = Taxa.query.filter_by(taxonInt=taxonInt).first()
                    if taxon:
                        # get scientific name
                        scientificName = taxon.scientificName
                        # Check that a specimen have been scanned after the taxon
                        if len(det.splitlines()) > 1:
                            # For each specimen identified to the current taxon, add record to database (populate Occurrences)
                            for specimen in det.splitlines()[1:]:
                                # Remove NHMO shit
                                specimen = specimen.replace("http://purl.org/nhmuio/id/", "") # Remove NHMO shit
                                # For handeling the qr-code-data delimited by semicolon ';'. This piece can be removed after a while when all specimens with such labels are in the database. 
                                specimen2 = specimen
                                if re.search("\;", specimen2):
                                    specimen2_event = specimen2.split(";")[0]
                                    specimen2 = "TMU:"+specimen2_event+":"
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
                                    # If the scientific name has changed 
                                    # create a new identification-event-record and update Occurrence-record
                                    if identification.scientificName != scientificName:
                                        new_identification = new_id()
                                        db.session.add(new_identification)
                                        # Commit new identification
                                        id_count+=1
                                        db.session.commit()
                                        db.session.refresh(new_identification)
                                        occurrence.identificationID = new_identification.identificationID
                                        occurrence.unit_id = unit_id
                                    # If Identification_event exists and the scientific name is the same as before, update the unit-ID
                                    else:
                                        occurrence.unit_id = unit_id
                                    # Commit 
                                    occ_update_count+=1
                                    db.session.commit()
                                # If occurrenceID not exist and if eventID exist create a new occurrence-record:
                                elif Collecting_events.query.filter_by(eventID=specimen2.split(":")[1]).first() or Collecting_events.query.filter_by(eventID=specimen2.split(":")[1].replace("_A", "")).first(): # The last query where "_A" is removed is to find a few eventIDs that where changed by a mistake. This can be removed after a while when the relevant specimens have been databased
                                    # First create the Identification-record
                                    new_identification = new_id()
                                    db.session.add(new_identification)
                                    # Commit new identification
                                    id_count+=1
                                    db.session.commit()
                                    db.session.refresh(new_identification)
                                    # This code can be removed after a while: If this is one of the events where "_A" were removed from the eventID by an accident, remove the "_A" from the eventID
                                    if Collecting_events.query.filter_by(eventID=specimen2.split(":")[1]).first():
                                        eventID = specimen2.split(":")[1]
                                    else:
                                        eventID = specimen2.split(":")[1].replace("_A", "")
                                    # Then the Occurrence-record
                                    new_occurrence=Occurrences(
                                        occurrenceID = specimen,
                                        catalogNumber = specimen2.split(":")[2],
                                        eventID = eventID,
                                        identificationID = new_identification.identificationID,
                                        ownerInstitutionCode = specimen2.split(":")[0],
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
                        else:
                            flash(f'No specimen scanned after {scientificName}', category="error")
                    else:
                        flash(
                            f'{scientificName} does not exist in database', category="error")
        else:
            flash("A determination should be inserted!", category="error")
        if occ_count > 0:
            flash(f'Occurrences added: {occ_count}')
        if occ_update_count > 0:
            flash(f'Occurrences updated: {occ_update_count}')
        if id_count > 0:
            flash(f'Identifications added: {id_count}')
    # Return html-page
    return render_template("specimen_det.html", title=title, user=current_user, entomologists=entomologists, taxa=taxa, decoded_QR_codes=decoded_QR_codes)

# Add determinations to database. Add specimens to database if not already present.
@specimens.route('/send_decoded_QR_codes/<string:decoded_QR_codes>/', methods=["POST", "GET"])
@login_required
def send_decoded_QR_codes(decoded_QR_codes):
    title = "New determinations"
    decoded_QR_codes=decoded_QR_codes
    entomologists = Collectors.query.all()
    # Return html-page
    return render_template("specimen_det.html", title=title, user=current_user, entomologists=entomologists, decoded_QR_codes=decoded_QR_codes)


# Query database for specimen-data and render a specimen-table 
@specimens.route('/specimen_view/<string:occurrence_id>/', methods=['GET'])
@login_required
def specimen_view(occurrence_id):
    title = "Specimen page"
    # Query Occurrence data
    occurrence = Occurrences.query.filter_by(occurrenceID=occurrence_id)\
            .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
            .join(Country_codes, Collecting_events.countryCode==Country_codes.countryCode)\
            .join(co1, Occurrences.occurrenceID==co1.occurrenceID, isouter=True)\
            .join(Eunis_habitats, Collecting_events.eunisCode==Eunis_habitats.eunisCode, isouter=True)\
            .with_entities(Occurrences.occurrenceID, Occurrences.identificationID, Occurrences.catalogNumber, Occurrences.individualCount, 
            Occurrences.preparations, Occurrences.occurrenceRemarks, Occurrences.associatedTaxa, 
            Occurrences.associatedReferences, Occurrences.ownerInstitutionCode, Occurrences.verbatimLabel,
            Country_codes.country, Collecting_events.eventID, Collecting_events.municipality,
            Collecting_events.locality_1, Collecting_events.locality_2, Collecting_events.habitat, Collecting_events.substrateName, 
            Collecting_events.substratePlantPart, Collecting_events.substrateType, Collecting_events.eventDate_1, 
            Collecting_events.eventDate_2, Collecting_events.samplingProtocol, Collecting_events.recordedBy, Collecting_events.decimalLatitude, 
            Collecting_events.decimalLongitude, Collecting_events.coordinateUncertaintyInMeters, Collecting_events.eventRemarks,
            co1.sequenceID, co1.sequence, co1.source, co1.sequence_length, Eunis_habitats.eunisCode, Eunis_habitats.habitatName)\
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
