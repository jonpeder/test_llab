# load packages
from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_required, current_user
import sqlite3
from .models import User, Collectors, Occurrences, Taxa, Identification_events
from . import db
import re
import datetime

# connect to __init__ file
specimens = Blueprint('specimens', __name__)

# Add determinations to database. Add specimen to database if not already present.


@specimens.route('/det', methods=["POST", "GET"])
@login_required
def det():
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

        #
        #unit_id = db.Column(db.String(80))
        #dateIdentified = db.Column(db.String)
        #createdByUserID = db.Column(db.String(20), db.ForeignKey('user.id'))

         # eventID =
         #catalogNumber = db.Column(db.String(20))
    # Return html-page
    return render_template("det.html", title=title, user=current_user, entomologists=entomologists)
