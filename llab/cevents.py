# load packages
from .functions import newEventID
from flask import Blueprint, current_app, redirect, url_for, request, render_template, flash
from flask_login import login_required, current_user
from .models import User, Collectors, Collecting_events, Country_codes, Collecting_methods, Print_events, Event_images
from . import db
import os
from os import path
from os.path import exists
import qrcode
import uuid
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


@cevents.route('/new_event', methods=["POST", "GET"])
@login_required
def new_event():
    title = "New collecting event"
    global substrate_type
    global substrate_part
    # Finn innsamlingsmetode og innsamlere
    leg = Collectors.query.all()
    met = Collecting_methods.query.all()
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
    return render_template("new_event.html", title=title, loc=loc, latlon=latlon, substrate_types=substrate_types, substrate_parts=substrate_parts, date=date, new_ID=new_ID, met=met, leg=leg, user=current_user)


@cevents.route('/show_event', methods=['GET', 'POST'])
@login_required
def show_event():
    title = "Show collecting events"
    events = Collecting_events.query.filter_by(
        createdByUserID=current_user.id).order_by(Collecting_events.eventID.desc())
    event = ""
    if request.method == 'POST':
        eventID = request.form.get("eventID")
        event = Collecting_events.query.filter_by(eventID=eventID).first()
        files = Event_images.query.filter_by(eventID=eventID).all()
        if eventID:
            # Button 2: Edit event
            if request.form.get('action2') == 'VALUE2':
                title = "Edit collecting events"
                leg = Collectors.query.all()
                met = Collecting_methods.query.all()
                return render_template("edit_event.html", title=title, user=current_user, files=files, event=event, leg=leg, met=met, substrate_parts=substrate_parts, substrate_types=substrate_types)
            # Button 1: Show event
            else:
                return render_template("show_event.html", title=title, user=current_user, events=events, files=files, event=event)
        else:
            return render_template("show_event.html", title=title, user=current_user, events=events, event=event)
    else:
        return render_template("show_event.html", title=title, user=current_user, events=events, event=event)


@cevents.route('/edit_event', methods=['GET', 'POST'])
@login_required
def edit_event():
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
            event.eventDate_1 = eventDate_1
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
            return redirect(url_for('cevents.show_event'))
        else:
            # Go back to original page
            return redirect(url_for('cevents.show_event'))
    else:
        # Go back to original page
        return redirect(url_for('cevents.show_event'))


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
                    .join(Collecting_methods, Collecting_events.samplingProtocol == Collecting_methods.ID)\
                    .add_columns(Collecting_events.eventID, Collecting_events.countryCode, Collecting_events.county, Collecting_events.strand_id, Collecting_events.municipality, Collecting_events.locality_1, Collecting_events.locality_2, Collecting_events.habitat,Collecting_events.substrateName,Collecting_events.substratePlantPart,Collecting_events.substrateType, Collecting_events.decimalLatitude, Collecting_events.decimalLongitude, Collecting_events.coordinateUncertaintyInMeters, Collecting_events.eventDate_1, Collecting_events.eventDate_2, Collecting_methods.samplingProtocol, Collecting_methods.ID.label("samplingProtocol_app"), Collecting_events.recordedBy)\
                    .filter(Collecting_events.eventID.in_([event.eventID for event in events]))\
                    .order_by(Collecting_events.eventID.desc())\
                    .all()
                # Create qrcodes
                for event in events:
                    for data in event_data:
                        if event.eventID==data.eventID:
                            for n in range(event.print_n):
                                filename = f'{current_user.id}_qrlabel_{event.eventID}_{n}.png'
                                qr = qrcode.QRCode(version = 1, box_size = 5, border = 1, error_correction=qrcode.constants.ERROR_CORRECT_L)
                                qr.add_data(f'{event.eventID};{uuid.uuid4()}')
                                qr.make(fit = True)
                                img = qr.make_image(fill_color = 'black', back_color = 'white')
                                img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Return labels
                return render_template("label_output.html", title=title, events=events, user=current_user, event_data=event_data)

    # Søk etter event-IDer
    events = Collecting_events.query.filter_by(createdByUserID = current_user.id).order_by(Collecting_events.eventID.desc())
    # Return
    return render_template("event_labels.html", title = title, events=events, user=current_user)
