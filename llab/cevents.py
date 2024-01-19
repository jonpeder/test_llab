# load packages
from .functions import newEventID, bar_plot_dict
from flask import Blueprint, current_app, redirect, url_for, request, render_template, flash
from flask_login import login_required, current_user
from .models import User, Collectors, Collecting_events, Country_codes, Print_events, Event_images, Catalog_number_counter, Occurrences, Identification_events, Taxa
from . import db
import os
from os import path
from os.path import exists
import qrcode
import sqlalchemy
import uuid
import pandas as pd
#import pdfkit
#import subprocess

# connect to __init__ file
cevents = Blueprint('cevents', __name__)

# Specify app
app = current_app

# Variables for creating form loops
loc = ["County", "Region_abbr", "Municipality",
       "Locality_1", "Locality_2", "Habitat"]
latlon = ["Latitude", "Longitude", "Radius"]
date = ["Date_1", "Date_2"]
substrate_types = ["gall", "mine", "colony"]
substrate_parts = ["flower", "stem", "leaf", "shoot", "twig", "root",
                  "fruit", "seed", "cone", "female_catkin", "male_catkin", "fruitbody"]
met = ["Sweep-net","Reared","Malaise-trap","Hand-picked","Light-trap","Slam-trap","Window-trap","Color-pan","Yellow-pan","White-pan"]


@cevents.route('/event_new', methods=["POST", "GET"])
@login_required
def event_new():
    title = "New collecting event"
    global substrate_type
    global substrate_part
    # Finn innsamlingsmetode, innsamlere og land
    leg = Collectors.query.all()
    ctries = Country_codes.query.all()
    # If a for is posted, update database before generating the new page
    if request.method == 'POST':
        # Get input from form
        eventID = request.form.get("ID")
        countryCode = request.form.get("Country")
        stateProvince = ""
        county = request.form.get("County")
        strand_id = request.form.get("Region_abbr")
        municipality = request.form.get("Municipality")
        locality_1 = request.form.get("Locality_1")
        locality_2 = request.form.get("Locality_2")
        habitat = request.form.get("Habitat")
        decimalLatitude = request.form.get("Latitude")
        decimalLongitude = request.form.get("Longitude")
        coordinateUncertaintyInMeters = request.form.get("Radius")
        samplingProtocol = request.form.get("Collecting_method")
        eventDate_1 = request.form.get("Date_1")
        eventDate_2 = request.form.get("Date_2")
        recordedBy = request.form.getlist("Collected_by")
        eventRemarks = request.form.get("Remarks")
        substrate_name = request.form.get("Substrate_name")
        substrate_type = request.form.get("Substrate_type")
        substrate_part = request.form.get("Substrate_part")
        # Button 2: Populate database with input from form
        if request.form.get('action2') == 'VALUE2':
            # Flash message if input eventID already exists
            already_existing_evnetID = Collecting_events.query.filter_by(
                eventID=eventID).first()
            if already_existing_evnetID:
                flash('event-ID aready exists', category='error')
            else:
                # Set date to NULL if not specified
                if not eventDate_1:
                    eventDate_1 = None #"0000-00-00"
                if not eventDate_2:
                    eventDate_2 = None #"0000-00-00"
                # new Collecting_events object
                new_event = Collecting_events(eventID=eventID, countryCode=countryCode, stateProvince=stateProvince, county=county, strand_id=strand_id, municipality=municipality, locality_1=locality_1, locality_2=locality_2, habitat=habitat, decimalLatitude=decimalLatitude, decimalLongitude=decimalLongitude,
                                              coordinateUncertaintyInMeters=coordinateUncertaintyInMeters, samplingProtocol=samplingProtocol, eventDate_1=eventDate_1, eventDate_2=eventDate_2, recordedBy=" | ".join(recordedBy), eventRemarks=eventRemarks, createdByUserID=current_user.id, substrateName=substrate_name, substrateType=substrate_type, substratePlantPart=substrate_part)
                # Add new objects to database
                db.session.add(new_event)
                # Commit
                db.session.commit()
                flash(
                    f'Collecting event with event-ID {eventID} created!', category="success")
    # Suggest new eventID
    events = Collecting_events.query.all()
    IDs = []
    for i in events:
        IDs.append(i.eventID)
    new_ID = newEventID(IDs, current_user.initials)
    # Return html-page
    return render_template("event_new.html", title=title, loc=loc, latlon=latlon, substrate_types=substrate_types, substrate_parts=substrate_parts, date=date, new_ID=new_ID, met=met, leg=leg, ctries=ctries, user=current_user)


@cevents.route('/event_show', methods=['GET', 'POST'])
@login_required
def event_show():
    title = "Collecting events"
    events = Collecting_events.query.filter_by(
        createdByUserID=current_user.id).order_by(Collecting_events.eventID.desc())
    if request.method == 'POST':
        eventID = request.form.get("eventID")
        event = Collecting_events.query.filter_by(eventID=eventID).first()
        files = Event_images.query.filter_by(eventID=eventID).all()
        if eventID:
            # Button 2: Edit event
            if request.form.get('action2') == 'VALUE2':
                title = "Edit event"
                leg = Collectors.query.all()
                return render_template("event_edit.html", title=title, user=current_user, files=files, event=event, leg=leg, met=met, substrate_parts=substrate_parts, substrate_types=substrate_types)
            # Button 1: Show event
            else:
                return render_template("event_show.html", title=title, user=current_user, events=events, files=files, event=event)
        else:
            return render_template("event_show.html", title=title, user=current_user, events=events, event=event)
    else:
        event = ""
        return render_template("event_show.html", title=title, user=current_user, events=events, event=event)


@cevents.route('/event_edit', methods=['GET', 'POST'])
@login_required
def event_edit():
    title = "Edit collecting events"
    if request.method == 'POST':
        if request.form.get('action1') == 'VALUE1':
            # Get input from form
            # Collecting event
            eventID = request.form.get("eventID")
            countryCode = request.form.get("countryCode")
            stateProvince = request.form.get("stateProvince")
            county = request.form.get("county")
            strand_id = request.form.get("strand_code")
            municipality = request.form.get("municipality")
            locality_1 = request.form.get("locality_1")
            locality_2 = request.form.get("locality_2")
            habitat = request.form.get("habitat")
            decimalLatitude = request.form.get("decimalLatitude")
            decimalLongitude = request.form.get("decimalLongitude")
            coordinateUncertaintyInMeters = request.form.get(
                "coordinateUncertaintyInMeters")
            samplingProtocol = request.form.get("samplingProtocol")
            eventDate_1 = request.form.get("eventDate_1")
            eventDate_2 = request.form.get("eventDate_2")
            recordedBy = " | ".join(request.form.getlist("recordedBy"))
            eventRemarks = request.form.get("eventRemarks")
            substrateName = request.form.get("substrateName")
            substratePlantPart = request.form.get("substratePlantPart")
            substrateType = request.form.get("substrateType")
            # Event images
            images = Event_images.query.filter_by(eventID=eventID).all()
            for image in images:
                image_update = Event_images.query.filter_by(id=image.id).first()
                if request.form.get(f'{image.id}_{image.filename}'):
                    category=request.form.get(f'{image.id}_imageCategory')
                    comment=request.form.get(f'{image.id}_comment')
                    # Update image-record
                    image_update.imageCategory = category
                    image_update.comment = comment
                    #flash(f'{image.filename} updated!', category="success")
                else:
                    # delete image-record
                    db.session.delete(image_update)
                    #flash(f'{image.filename} deleted!', category="error")
                db.session.commit()
            # Update event-record
            event = Collecting_events.query.filter_by(eventID=eventID).first()
            event.countryCode = countryCode
            event.stateProvince = stateProvince
            event.county = county
            event.strand_id = strand_id
            event.municipality = municipality
            event.locality_1 = locality_1
            event.locality_2 = locality_2
            event.habitat = habitat
            event.decimalLatitude = decimalLatitude
            event.decimalLongitude = decimalLongitude
            event.coordinateUncertaintyInMeters = coordinateUncertaintyInMeters
            event.samplingProtocol = samplingProtocol
            if not eventDate_1:
                event.eventDate_1 = None
            else:
                event.eventDate_1 = eventDate_1
            if not eventDate_2:
                event.eventDate_2 = None
            else:
                event.eventDate_2 = eventDate_2
            event.recordedBy = recordedBy
            event.eventRemarks = eventRemarks
            event.substrateName = substrateName
            event.substratePlantPart = substratePlantPart
            event.substrateType = substrateType
            db.session.commit()
            flash(
                f'Collecting event with event-ID {eventID} updated!', category="success")
            # Go back to original page
            return redirect(url_for('cevents.event_show'))
        else:
            # Go back to original page
            return redirect(url_for('cevents.event_show'))
    else:
        # Go back to original page
        return redirect(url_for('cevents.event_show'))


@cevents.route('/event_labels', methods=["POST", "GET"])
@login_required
def labels():
    title = "Print specimen labels"
    # Remove earlier qr-code image-files
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    for file in files:
        if file.startswith(f'{current_user.id}_qrlabel_'):
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], file))
    # Post
    if request.method == 'POST':
        # Button 1: Add eventID and number of labels to be printed
        if request.form.get('action1') == 'VALUE1':
            # Get data from form
            eventID = request.form.get("ID")
            label_number = request.form.get("Label_number")
            # Add new eventID to temporary databse
            new_event = Print_events(
                eventID=eventID, print_n=label_number, createdByUserID=current_user.id)
            db.session.add(new_event)
            db.session.commit()
        # Button 2: Clear table
        if request.form.get('action2') == 'VALUE2':
            # Delete all records in print_events table
            Print_events.query.filter_by(
                createdByUserID=current_user.id).delete()
            db.session.commit()
        # Button 3: Print lables
        if request.form.get('action3') == 'VALUE3':
            # Finn eventIDer og antall etiketter som skal printes av brukeren
            user = current_user
            events = user.print_events
            # Dersom ingen event-id er valgt
            if not events:
                flash("At least one collecting event must be added", category="error")
            else:
                # Query collecting-event-data for selected eventIDs
                event_data = Collecting_events.query\
                    .filter(Collecting_events.eventID.in_([event.eventID for event in events]))\
                    .order_by(Collecting_events.eventID.desc())\
                    .all()
                # For each label create qr-code
                catalog_numbers = {} # Dictionary for catalog-numbers
                for event in events:
                    for data in event_data:
                        if event.eventID==data.eventID:
                            for n in range(event.print_n):
                                # Add record to catalg_number_counter
                                new_number = Catalog_number_counter()
                                db.session.add(new_number)
                                db.session.commit()
                                db.session.refresh(new_number)
                                catalog_number = current_user.initials + "-" + "{:0>6}".format(new_number.id)
                                # Add catalog-numbers to dictionary
                                catalog_numbers[f'{current_user.id}_{event.id}_{n}'] = catalog_number
                                # Create qr-code image files
                                filename = f'{current_user.id}_qrlabel_{event.id}_{n}.png'
                                qr = qrcode.QRCode(version = 1, box_size = 5, border = 1, error_correction=qrcode.constants.ERROR_CORRECT_L)
                                qr.add_data(f'{current_user.institutionCode}:{event.eventID}:{catalog_number}')
                                qr.make(fit = True)
                                img = qr.make_image(fill_color = 'black', back_color = 'white')
                                img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Return labels
                return render_template("event_labels_output.html", title=title, events=events, user=current_user, event_data=event_data, catalog_numbers=catalog_numbers)

    # Søk etter event-IDer
    events = Collecting_events.query.filter_by(createdByUserID = current_user.id).order_by(Collecting_events.eventID.desc())
    # Return
    return render_template("event_labels.html", title = title, events=events, user=current_user)


@cevents.route('/test_labels', methods=["POST", "GET"])
@login_required
def test_labels():
    return render_template("label_test_output.html", user=current_user)

@cevents.route('/', methods=["POST", "GET"])
@login_required
def home():
    ##
    # Collecting_events
    ##
    events = Collecting_events.query.all()
    # Create dataframe
    eventID = []
    samplingProtocol = []
    eventDate_1 = []
    databased = []
    for row in events:
        eventID.append(row.eventID)
        samplingProtocol.append(row.samplingProtocol)
        eventDate_1.append(row.eventDate_1)
        databased.append(row.databased)
    events = {"EventID":eventID, "samplingProtocol":samplingProtocol, "date":eventDate_1, "databased":databased}
    events_df = pd.DataFrame(events)
     # Yearly
    event_year = bar_plot_dict(events_df, "year", 0)
    # Monthly
    event_month = bar_plot_dict(events_df, "month", 0)
    ##
    # Occurrences
    ##
    occurrences = Occurrences.query\
            .join(Identification_events, Occurrences.identificationID==Identification_events.identificationID)\
            .join(Taxa, Identification_events.scientificName==Taxa.scientificName)\
            .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
            .with_entities(Occurrences.databased, Collecting_events.eventDate_1, Taxa.order, Taxa.family, Taxa.genus, Taxa.taxonRank, Collecting_events.samplingProtocol)\
            .all()
    # Create occurrence dataframe
    family = []
    order = []
    genus = []
    taxonRank = []
    samplingProtocol = []
    eventDate_1 = []
    databased = []
    for row in occurrences:
        family.append(row.family)
        order.append(row.order)
        genus.append(row.genus)
        taxonRank.append(row.taxonRank)
        samplingProtocol.append(row.samplingProtocol)
        eventDate_1.append(row.eventDate_1)
        databased.append(row.databased)
    occurrences_dict = {"family":family, "order":order, "genus":genus, "taxonRank":taxonRank,"samplingProtocol":samplingProtocol, "date":eventDate_1, "databased":databased}
    occurrences_df = pd.DataFrame(occurrences_dict)
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
    ##
    # Identifications
    ##
    identification = Identification_events.query.all()
    # Create dataframe
    dateIdentified = []
    for row in identification:
        dateIdentified.append(row.dateIdentified)
    identification = {"date":dateIdentified}
    identification_df = pd.DataFrame(identification)
    # Yearly
    identification_year = bar_plot_dict(identification_df, "year", 0)

    return render_template("home.html", user=current_user, event_year=event_year, event_month=event_month, occurrence_year=occurrence_year, occurrence_month=occurrence_month, occurrence_method=occurrence_method, occurrence_order=occurrence_order, occurrence_family=occurrence_family, occurrence_genus=occurrence_genus, occurrence_taxonRank=occurrence_taxonRank, identification_year=identification_year)