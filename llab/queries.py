from flask import Blueprint, current_app, flash, request, redirect, url_for, render_template, send_from_directory
from flask_login import login_required, current_user
from .models import User, Collecting_events, Event_images, Taxa, Occurrences, Occurrence_images, Collectors, Collecting_methods
from . import db
import os
import numpy as np

# connect to __init__ file
queries = Blueprint('queries', __name__)

@queries.route('/show_event', methods=['GET', 'POST'])
@login_required
def show_event():
    title = "Show collecting events"
    events = Collecting_events.query.filter_by(createdByUserID=current_user.id).order_by(Collecting_events.eventID.desc())
    event=""
    if request.method == 'POST':
        eventID = request.form.get("eventID")
        event = Collecting_events.query.filter_by(eventID=eventID)
        files = Event_images.query.filter_by(eventID=eventID)
        # Button 1:
        if request.form.get('action1') == 'VALUE1':
            return render_template("show_event.html", title=title, user=current_user, files=files, events=events, event=event)
        # Button 2:
        leg = Collectors.query.all()
        met = Collecting_methods.query.all()
        if request.form.get('action2') == 'VALUE2':
            title = "Edit collecting events"
            return render_template("edit_event.html", title=title, user=current_user, files=files, event=event, leg=leg, met=met)
    else:
        return render_template("show_event.html", title=title, user=current_user, events=events, event=event)

    
@queries.route('/edit_event', methods=['GET', 'POST'])
@login_required
def edit_event():
    title = "Edit collecting events"
    if request.method == 'POST':
        # Get data from form
        # Get input from form
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
        coordinateUncertaintyInMeters = request.form.get("coordinateUncertaintyInMeters")
        samplingProtocol = request.form.get("samplingProtocol")
        eventDate_1 = request.form.get("eventDate_1")
        eventDate_2 = request.form.get("eventDate_2")
        recordedBy = " | ".join(request.form.getlist("recordedBy"))
        eventRemarks = request.form.get("eventRemarks")
        substrate_name = request.form.get("substrate_name")
        substrate_type = request.form.get("substrate_type")
        substrate_part = request.form.get("substrate_part")
        # Update record
        event = Collecting_events.query.filter_by(eventID=eventID).first()
        event.countryCode=countryCode
        event.stateProvince=stateProvince
        event.county=county
        event.strand_id=strand_id
        event.municipality=municipality
        event.locality_1=locality_1
        event.locality_2=locality_2
        event.habitat=habitat
        event.decimalLatitude=decimalLatitude
        event.decimalLongitude=decimalLongitude
        event.coordinateUncertaintyInMeters=coordinateUncertaintyInMeters
        event.samplingProtocol=samplingProtocol
        event.eventDate_1=eventDate_1
        event.eventDate_2=eventDate_2
        event.recordedBy=recordedBy
        event.eventRemarks=eventRemarks
        event.substrate_name=substrate_name
        event.substrate_type=substrate_type
        event.substrate_part=substrate_part
        # Update database
        #print(eventID)
        #print(countryCode)
        #print(county)
        #print(habitat)
        print(coordinateUncertaintyInMeters)
        
        db.session.commit()
        flash(f'Collecting event with event-ID {eventID} updated!', category="success")
        # Go back to original page
        return redirect(url_for('queries.show_event'))
    else:
        return render_template("show_event.html", title=title, user=current_user, events=events)

    
@queries.route('/taxon_image', methods=['GET', 'POST'])
@login_required
def taxon_image():
    title = "Taxon images"
    imagecat = ['habitus', 'in-situ', 'lateral', 'ventral', 'dorsal', 'face', 'fore-wing', 'hind-wing']
    # Prepare list of taxa for dropdown-select-search bar 
    taxa = Taxa.query.all() # Database query for taxa
    order = tuple(np.unique([i.order for i in taxa if i.order]))
    family = tuple(np.unique([i.family for i in taxa if i.family]))
    genus = tuple(np.unique([i.genus for i in taxa if i.genus]))
    scientificName = tuple(np.unique([i.scientificName for i in taxa]))
    dropdown_names = order+family+genus+scientificName
    dropdown_ranks = tuple(len(order)*["order"]+len(family)*["family"]+len(genus)*["genus"]+len(scientificName)*["scientificName"])

    # POST REQUEST
    if request.method == 'POST':
        # Get input
        taxa = request.form.getlist("taxon_name")
        image_categories = request.form.getlist("image_categories")
        print(image_categories)
        # Use all image categories if no image category is selected
        if not image_categories:
            image_categories = imagecat
        # Loop over selected taxa and get scientific names of (children) species
        scientific_names = list()
        for i in taxa:
            taxon = i.split(";")
            # Query occurrences of given taxon
            if (taxon[1] == "scientificName"):
                scientific_names_tmp = taxon[0]
            else:
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
        occurrences_db = Occurrences.query.filter(Occurrences.scientificName.in_(scientific_names)).all()
        occurrence_ids = tuple(np.unique([i.occurrenceID for i in occurrences_db if i.occurrenceID]))

        # Get images for selected taxa
        images = Occurrence_images.query\
            .join(Occurrences, Occurrence_images.occurrenceID==Occurrences.occurrenceID)\
            .add_columns(Occurrence_images.filename, Occurrence_images.imageCategory, Occurrence_images.comment, Occurrence_images.occurrenceID, Occurrences.scientificName)\
            .filter(Occurrence_images.occurrenceID.in_(occurrence_ids))\
            .filter(Occurrence_images.imageCategory.in_(image_categories))\
            .all()
        
        # list of occurrenceIDs associated with images
        occurrenceIDs_imaged = [i.occurrenceID for i in images if i.occurrenceID]
        # taxa associated with occurrenceIDs
        imaged_taxa = Taxa.query\
            .join(Occurrences, Taxa.scientificName==Occurrences.scientificName)\
            .add_columns(Taxa.scientificName, Taxa.taxonRank, Taxa.genus, Taxa.specificEpithet, Taxa.scientificNameAuthorship)\
            .filter(Occurrences.occurrenceID.in_(occurrenceIDs_imaged))\
            .all()

        # Button 1:
        #if request.form.get('action1') == 'VALUE1':
            #event = Collecting_events.query.filter_by(eventID=eventID)
            #files = Event_images.query.filter_by(eventID=eventID)
        return render_template("taxon_image.html", title=title, user=current_user, dropdown_names=dropdown_names, dropdown_ranks=dropdown_ranks, imagecat=imagecat, images=images, imaged_taxa=imaged_taxa)
    else:
        return render_template("taxon_image.html", title=title, user=current_user, dropdown_names=dropdown_names, dropdown_ranks=dropdown_ranks, imagecat=imagecat)
