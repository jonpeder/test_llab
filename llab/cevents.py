# load packages
from flask import Blueprint, redirect, url_for, escape, request, render_template, send_file, flash, jsonify
from flask_login import login_required, current_user
import sqlite3
from .models import User, Collectors, Collecting_events, Country_codes, Collecting_methods, Print_events
from . import db
import subprocess
import time
import os
from os import path
from os.path import exists
import json
import sys


# connect to __init__ file
cevents = Blueprint('cevents', __name__)

# Load python functions
from .functions import newEventID, readstrand

# Variables for creating form loops
loc = ["County", "Strand_code", "Municipality", "Locality_1", "Locality_2", "Habitat"]
latlon = ["Latitude", "Longitude", "Radius"]
date = ["Date_1", "Date_2"]
LOC = ["", "", "", "", "", ""]
LATLON = ["", "", ""]
DATE = ["", ""]
substrate_type = ["gall", "mine", "colony"]
substrate_part = ["flower", "stem", "leaf", "shoot", "twig", "root", "fruit", "seed", "cone", "female_catkin", "male_catkin", "fruitbody"]

@cevents.route('/new_event', methods=["POST", "GET"])
@login_required
def new_event():
    title = "New collecting event"
    global substrate_type
    global substrate_part
    ## Finn innsamlingsmetode og innsamlere
    leg = Collectors.query.all()
    met = Collecting_methods.query.all()
    # If a for is posted, update database before generating the new page
    if request.method == 'POST':
        # Get input from form
        eventID = request.form.get("ID")
        countryCode = request.form.get("Country")
        stateProvince = ""
        county = request.form.get("County")
        strand_id = request.form.get("Strand_code")
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
        substrate_plant_part = request.form.get("Substrate_plant_part")

        # Create global variables for remembering input from last post
        global LOC
        global LATLON
        global DATE
        LOC = ["", "", "", "", "", ""]
        LATLON = ["", "", ""]
        DATE = ["", ""]

        # Button 1: Get input coordinates from form and find locality data based on coordinates
        if request.form.get('action1') == 'VALUE1':
            strand = readstrand(r_script_path='/home/jon/Dropbox/python/web_apps/llab/llab//R/strandr.R', lat=decimalLatitude, lon=decimalLongitude)
            strand_id = strand[0]
            municipality = strand[1]
            county = strand[2]
            locality_2 = strand[3]
            # Fix problem with county 'Oslo og Akershus'
            if county == 'Akershus og Oslo':
                if municipality == 'Oslo':
                    county = 'Oslo'
                else:
                    county = 'Akershus'
            # Add to variables
            LOC = [county, strand_id, municipality, locality_1, locality_2, habitat]
            LATLON = [decimalLatitude, decimalLongitude, coordinateUncertaintyInMeters]
            DATE = [eventDate_1, eventDate_2]

        # Button 2: Populate database with input from form
        if request.form.get('action2') == 'VALUE2':
            # Flash message if input eventID already exists
            already_existing_evnetID = Collecting_events.query.filter_by(eventID=eventID).first()
            if already_existing_evnetID:
                flash('event-ID aready exists', category='error')
            else:
                # new Collecting_events object
                new_event = Collecting_events(eventID=eventID, countryCode=countryCode, stateProvince=stateProvince, county=county, strand_id=strand_id, municipality=municipality, locality_1=locality_1, locality_2=locality_2, habitat=habitat, decimalLatitude=decimalLatitude, decimalLongitude=decimalLongitude, coordinateUncertaintyInMeters=coordinateUncertaintyInMeters,samplingProtocol=samplingProtocol, eventDate_1=eventDate_1, eventDate_2=eventDate_2, recordedBy=" | ".join(recordedBy), eventRemarks=eventRemarks, createdByUserID=current_user.id, substrateName=substrate_name, substrateType=substrate_type, substratePlantPart=substrate_plant_part)
                # Add new objects to database
                db.session.add(new_event)
                # Commit
                db.session.commit()
                flash(f'Collecting event with event-ID {eventID} created!', category="success")
    
    # Suggest new eventID
    events = Collecting_events.query.all()
    IDs = [] 
    for i in events:
        IDs.append(i.eventID)
    new_ID = newEventID(IDs, current_user.initials)
    
    # Return html-page
    return render_template("new_event.html", title=title, loc=loc, latlon=latlon, substrate_type=substrate_type, substrate_part=substrate_part, date=date, new_ID=new_ID, met=met, leg=leg, LOC = LOC, LATLON = LATLON, DATE=DATE, user=current_user)

@cevents.route('/event_labels', methods=["POST", "GET"])
@login_required
def labels():
    title = "Print specimen labels"
    # Post
    if request.method == 'POST':
        # Button 1: Add eventID and number of labels to be printed
        if request.form.get('action1') == 'VALUE1':
            # Get data from form
            eventID = request.form.get("ID")
            label_number = request.form.get("Label_number")
            # Add new eventID to temporary databse
            new_event = Print_events(eventID=eventID, print_n=label_number, createdByUserID = current_user.id)
            db.session.add(new_event)
            db.session.commit()
        # Button 2: Clear table
        if request.form.get('action2') == 'VALUE2':
            # Delete all records in print_events table
            #db.session.query(Print_events).filter_by(createdByUserID = current_user.id).delete()
            Print_events.query.filter_by(createdByUserID = current_user.id).delete()
            db.session.commit()
        # Button 3: Print lables
        if request.form.get('action3') == 'VALUE3':
            label_type = request.form.get("label_type")
            # Finn eventIDer og antall etiketter som skal printes av brukeren
            user = current_user
            e,n = [],[]
            cnt = 0
            for event in user.print_events:
                e.append(event.eventID)
                n.append(str(event.print_n))
                cnt += 1
            eventids = ','.join(e)
            labeln = ','.join(n)
            if cnt == 0:
                flash("At least one collecting event must be added", category="error")
            else:
                # Print labels
                process = subprocess.Popen(["/home/jon/Dropbox/python/web_apps/llab/llab/R/labels_exe.R", eventids, labeln, label_type, f'{current_user.id}_labels.pdf'])
                process.wait()
                return redirect(url_for('cevents.label_output'))

    # Søk etter event-IDer
    events = Collecting_events.query.filter_by(createdByUserID = current_user.id).order_by(Collecting_events.eventID.desc())
    # Return
    return render_template("event_labels.html", title = title, events=events, user=current_user)

@cevents.route('/label_output')
@login_required
def label_output():
    time.sleep(1)
    return send_file(f'/var/www/llab/llab/insect_labels/{current_user.id}_labels.pdf')
