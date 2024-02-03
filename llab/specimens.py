# load packages
from .functions import bar_plot_dict
from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_required, current_user
import sqlite3
from .models import User, Collectors, Occurrences, Taxa, Identification_events, Collecting_events, Country_codes, Eunis_habitats
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
    title = "New determinations"
    entomologists = Collectors.query.all()
    # If decoded_QR_codes is not specified
    decoded_QR_codes = ""
    # Count
    occ_count=0
    occ_update_count=0
    id_count=0
    # POST
    if request.method == 'POST':
        # Mandatory fields
        qr_data = request.form.get("qr_data")
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
        # Check that a det label have been scanned, that  ".det" is present in string
        print(qr_data)
        if re.search("det\.", qr_data):
            # For each taxon
            for det in qr_data.split("det."):
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
                    else:
                        sex = sex_tmp
                    # Get unit-ID
                    unit_id = det_data.split(":")[3]
                    # Check that the taxon exists in Taxa-table
                    taxon = Taxa.query.filter_by(taxonInt=taxonInt).first()
                    if taxon:
                        # get scientific name
                        scientificName = taxon.scientificName
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
                                elif Collecting_events.query.filter_by(eventID=specimen.split(":")[1]).first():
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
                                        catalogNumber = specimen.split(":")[2],
                                        eventID = specimen.split(":")[1],
                                        identificationID = new_identification.identificationID,
                                        ownerInstitutionCode = specimen.split(":")[0],
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
    return render_template("specimen_det.html", title=title, user=current_user, entomologists=entomologists, decoded_QR_codes=decoded_QR_codes)

# Add determinations to database. Add specimens to database if not already present.
@specimens.route('/send_decoded_QR_codes/<string:decoded_QR_codes>/', methods=["POST", "GET"])
@login_required
def send_decoded_QR_codes(decoded_QR_codes):
    title = "New determinations"
    decoded_QR_codes=decoded_QR_codes
    entomologists = Collectors.query.all()
    # Return html-page
    return render_template("specimen_det.html", title=title, user=current_user, entomologists=entomologists, decoded_QR_codes=decoded_QR_codes)


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
    ranks = ['species', 'spnov', 'species-group', 'genus', 'tribe', 'subfamily', 'family', 'superfamily', 'infraorder', 'order', 'class', 'other']
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
    # Make database queries
    occurrences = Occurrences.query.filter(Occurrences.occurrenceID.in_(occurrence_ids))\
            .join(Identification_events, Occurrences.identificationID==Identification_events.identificationID, isouter=True)\
            .join(Taxa, Identification_events.scientificName==Taxa.scientificName, isouter=True)\
            .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID, isouter=True)\
            .join(Country_codes, Collecting_events.countryCode==Country_codes.countryCode, isouter=True)\
            .join(Eunis_habitats, Collecting_events.eunisCode==Eunis_habitats.eunisCode, isouter=True)\
            .with_entities(Occurrences.occurrenceID, Country_codes.country, Collecting_events.eventID,
            Collecting_events.municipality, Collecting_events.locality_1, Collecting_events.locality_2, 
            Collecting_events.habitat, Collecting_events.substrateName, Collecting_events.substratePlantPart, 
            Collecting_events.substrateType, Collecting_events.eventDate_1, Collecting_events.eventDate_2, 
            Collecting_events.samplingProtocol, Collecting_events.recordedBy, Taxa.scientificName, Taxa.genus, Taxa.family, 
            Taxa.order, Taxa.taxonRank, Taxa.scientificNameAuthorship, Identification_events.identifiedBy, 
            Identification_events.dateIdentified, Identification_events.identificationQualifier, Identification_events.sex, Eunis_habitats.level1, Eunis_habitats.level2)\
            .order_by(Taxa.scientificName, Collecting_events.eventID)\
            .all()
    ##
    # Leaflet
    ##
    # Take out unique event_ids and get coordinates
    event_ids = []
    for occurrence in occurrences:
        if occurrence.eventID not in event_ids:
            event_ids.append(occurrence.eventID)
    events = Collecting_events.query.filter(Collecting_events.eventID.in_(event_ids)).all()
    ##
    # Statistics 
    ##
    # Eunis habitats
    eunis = Eunis_habitats.query.all()
    eunis_dict = {}
    for i in eunis:
        eunis_dict[i.eunisCode] = i.habitatName
    # Create occurrence dataframe
    family = []
    order = []
    genus = []
    taxonRank = []
    samplingProtocol = []
    eventDate_1 = []
    habitat1 = []
    habitat2 = []
    for row in occurrences:
        family.append(row.family)
        order.append(row.order)
        genus.append(row.genus)
        taxonRank.append(row.taxonRank)
        samplingProtocol.append(row.samplingProtocol)
        eventDate_1.append(row.eventDate_1)
        if row.level1:
            print(eunis_dict[row.level1])
            habitat1.append(eunis_dict[row.level1])
        else:
            habitat1.append("")
        if row.level2:
            habitat2.append(eunis_dict[row.level2])
        else:
            habitat2.append("")
    occurrences_dict = {"family":family, "order":order, "genus":genus, "taxonRank":taxonRank,"samplingProtocol":samplingProtocol, "date":eventDate_1, "habitat1":habitat1, "habitat2":habitat2}
    occurrences_df = pd.DataFrame(occurrences_dict)
    #print(occurrences_dict[])
    # Yearly
    occurrence_year = bar_plot_dict(occurrences_df, "year", 0)
    # Monthly
    occurrence_month = bar_plot_dict(occurrences_df, "month", 0)
    # Method
    occurrence_method = bar_plot_dict(occurrences_df, "samplingProtocol", 0)
    # Order
    occurrence_order = bar_plot_dict(occurrences_df, "order", 1)
    # Family
    occurrence_family = bar_plot_dict(occurrences_df, "family", 2)
    # Genus
    occurrence_genus = bar_plot_dict(occurrences_df, "genus", 0.5)
    # Rank
    occurrence_taxonRank = bar_plot_dict(occurrences_df, "taxonRank", 2)
    # Habitat level 1
    occurrence_habitat1 = bar_plot_dict(occurrences_df, "habitat1", 0)
    # Habitat level 2
    occurrence_habitat2 = bar_plot_dict(occurrences_df, "habitat2", 1)
    # Report if any of the specified occurrenceIDs are not present in database.
    for occurrence in occurrence_ids:
        if occurrence not in [i.occurrenceID for i in occurrences]:
            flash(f'{occurrence} not in database', category="error")
    # Return template
    return render_template("specimen_list.html", title=title, user=current_user, occurrences=occurrences, events=events, ranks=ranks, occurrence_year=occurrence_year, occurrence_month=occurrence_month, occurrence_method=occurrence_method, occurrence_habitat1=occurrence_habitat1, occurrence_habitat2=occurrence_habitat2, occurrence_order=occurrence_order, occurrence_family=occurrence_family, occurrence_genus=occurrence_genus, occurrence_taxonRank=occurrence_taxonRank)

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