# load packages
from .functions import bar_plot_dict
from flask import Blueprint, current_app, request, redirect, url_for, render_template, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from datetime import datetime
from .models import User, Collectors, Taxa, Country_codes, Observations, Collecting_events
from . import db
from .functions import compress_image
import uuid
import os
import numpy as np
import pandas as pd
import shutil
from werkzeug.utils import secure_filename

# connect to __init__ file
observations = Blueprint('observations', __name__)

# Specify app
app = current_app

# Specify allowed file extensions and define a function to control that input file is alowed
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#####
# Add determinations to database. Add specimens to database if not already present.
#####
@observations.route('/observation_add', methods=["POST", "GET"])
@login_required
def observation_add():
    # Path to image directory
    dir_path = "/var/www/llab/llab/static/images"
    #dir_path = "llab/static/images"
    # Get researchers
    entomologists = Collectors.query.all()
    # Get taxon data
    taxa = Taxa.query.all()
    # Get Country codes
    countries = Country_codes.query.all()
    # Get Event IDs
    events = Collecting_events.query.all()
    # POST
    if request.method == 'POST':
            occurrenceID=str(uuid.uuid4())
            taxonInt =  request.form.get("taxonInt")
            event_id = request.form.get("eventID")
            if event_id:
                event = Collecting_events.query.filter_by(eventID=event_id).first()
                decimalLatitude = event.decimalLatitude
                decimalLongitude = event.decimalLongitude
                coordinateUncertaintyInMeters = event.coordinateUncertaintyInMeters
                date = str(event.eventDate_1)
                countryCode = event.countryCode
                county = event.county
                municipality = event.municipality
                if event.locality_2:
                    locality = event.locality_1 + ", " + event.locality_2
                else:
                    locality = event.locality_1
                recordedBy = event.recordedBy
                occurrenceRemarks = event.samplingProtocol
                time = "12:00:00"
                eventDateTime = date+" "+time
            else:                
                decimalLatitude = round(float(request.form.get("Latitude")), 8)
                decimalLongitude =  round(float(request.form.get("Longitude")), 8)
                coordinateUncertaintyInMeters = request.form.get("uncertaintyInMeters")
                date = request.form.get("date")
                time = request.form.get("time")
                eventDateTime = date+" "+time
                countryCode = request.form.get("Country")
                county = request.form.get("County")
                municipality = request.form.get("Municipality")
                locality = request.form.get("Locality_2")
                recordedBy = request.form.get("recordedBy")
                occurrenceRemarks = request.form.get("occurrenceRemarks")
            identifiedBy = request.form.get("identifiedBy")
            lifeStage = request.form.get("lifeStage")
            individualCount = request.form.get("individualCount")
            sex = request.form.get("sex")
            # For each file in post request
            imageFileNames = []
            for file in request.files.getlist("files"):
                # If the user does not select a file
                if file.filename == '':
                    flash('No selected file', category="error")
                    return redirect(request.url)
                # Secure the filenames and save 
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename2 = f'{taxonInt}_{filename}'
                    if filename2 in os.listdir(f"{dir_path}/observations/"):
                        flash(f'Image allready exist under the filename{filename2}', category="error")
                        return redirect(request.url)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2)) # Save file to upload folder
                    shutil.copyfile(f"{app.config['UPLOAD_FOLDER']}/{filename2}", f"{dir_path}/observations/{filename2}") # Move file to image-folder
                    compress_image(os.path.join(app.config['UPLOAD_FOLDER'], filename2), f"{dir_path}/compressed/{filename2}", 20) # Save a compressed version of the image
                    os.remove(f"{app.config['UPLOAD_FOLDER']}/{filename2}") # Remove file from upload-folder
                    imageFileNames.append(filename2)
            # Join list of image filenames to string
            imageFileNames = ' | '.join(imageFileNames)
            # New database record
            new_observation = Observations(
                 occurrenceID = occurrenceID,
                 imageFileNames = imageFileNames,
                 taxonInt = taxonInt,
                 decimalLatitude = decimalLatitude,
                 decimalLongitude = decimalLongitude,
                 coordinateUncertaintyInMeters = coordinateUncertaintyInMeters,
                 eventDateTime = eventDateTime,
                 dateIdentified = date,
                 countryCode = countryCode,
                 county = county,
                 municipality = municipality,
                 locality = locality,
                 recordedBy = recordedBy,
                 identifiedBy = identifiedBy,
                 lifeStage = lifeStage,
                 individualCount = individualCount,
                 sex = sex,
                 occurrenceRemarks = occurrenceRemarks,
                 createdByUserID=current_user.id,
                 eventID = event_id)
            # Add new objects to database
            db.session.add(new_observation)
            # Commit
            db.session.commit()
            flash('Illustration added', category="success")
            return redirect(url_for("observations.observation_add")) 
    return render_template("observation_add.html", user=current_user, entomologists=entomologists, taxa=taxa, countries=countries, events=events)

#####
# Edit observation
#####
@observations.route('/observation_edit/<string:occurrence_id>/', methods=['POST', 'GET'])
@login_required
def observation_edit(occurrence_id):
    title = "Edit observation"
    # Path to image directory
    dir_path = "/var/www/llab/llab/static/images"
    # Get researchers
    entomologists = Collectors.query.all()
    # Get taxon data
    taxa = Taxa.query.all()
    # Get Country codes
    countries = Country_codes.query.all()
    # Get Event IDs
    events = Collecting_events.query.all()
    # Error handling
    try:
        # Get observation
        observation = Observations.query.filter_by(occurrenceID=occurrence_id)\
            .join(Country_codes, Observations.countryCode==Country_codes.countryCode, isouter=True)\
            .join(Taxa, Observations.taxonInt==Taxa.taxonInt, isouter=True)\
            .with_entities(Observations.occurrenceID, Observations.imageFileNames, Observations.eventDateTime, Observations.decimalLatitude, Observations.decimalLongitude, Observations.coordinateUncertaintyInMeters, Country_codes.countryCode, Country_codes.country, Observations.county, Observations.municipality, Observations.locality, Taxa.taxonInt, Taxa.taxonID, Taxa.taxonRank, Taxa.scientificName, Taxa.family, Taxa.order, Taxa.cl, Observations.individualCount, Observations.lifeStage, Observations.sex, Observations.recordedBy, Observations.identifiedBy, Observations.occurrenceRemarks, Observations.eventID)\
            .first()
        # separate date and time
        date = str(observation.eventDateTime).split(" ")[0]
        time = str(observation.eventDateTime).split(" ")[1]
        files = observation.imageFileNames.split(" | ")
        if request.method == 'POST':
            if request.form.get('action') == 'DELETE':
                # Get observation to delete
                observation_delete = Observations.query.filter_by(occurrenceID=occurrence_id).first()
                # Delete images
                for file in files:
                    try:
                        os.remove(f'{dir_path}/compressed/{file}')
                        os.remove(f'{dir_path}/observations/{file}')
                    except Exception as e:
                        app.logger.error(f"Error deleting image {file}: {str(e)}")
                        flash(f'Error deleting image {file}', category="error")
                # Delete observation
                db.session.delete(observation_delete)
                # Commit changes
                db.session.commit()
                flash(f'Observation deleted!', category="success")
                return redirect(url_for('observations.observation_filter'))
            if request.form.get('action') == 'CANCEL':
                return redirect(url_for('observations.observation_view', occurrence_id=occurrence_id))
            if request.form.get('action') == 'UPDATE':
                #imageFileNames = request.form.get("imageFileNames")
                taxonInt = request.form.get("taxonInt")
                event_id = request.form.get("eventID")
                if event_id:
                    event = Collecting_events.query.filter_by(eventID=event_id).first()
                    decimalLatitude = event.decimalLatitude
                    decimalLongitude = event.decimalLongitude
                    coordinateUncertaintyInMeters = event.coordinateUncertaintyInMeters
                    date = str(event.eventDate_1)
                    countryCode = event.countryCode
                    county = event.county
                    municipality = event.municipality
                    if event.locality_2:
                        locality = event.locality_1 + ", " + event.locality_2
                    else:
                        locality = event.locality_1
                    recordedBy = event.recordedBy
                    occurrenceRemarks = event.samplingProtocol
                    time = "12:00:00"
                    eventDateTime = date+" "+time
                else:                
                    decimalLatitude = round(float(request.form.get("Latitude")), 8)
                    decimalLongitude =  round(float(request.form.get("Longitude")), 8)
                    coordinateUncertaintyInMeters = request.form.get("uncertaintyInMeters")
                    date = request.form.get("date")
                    time = request.form.get("time")
                    eventDateTime = date+" "+time
                    countryCode = request.form.get("Country")
                    county = request.form.get("County")
                    municipality = request.form.get("Municipality")
                    locality = request.form.get("Locality_2")
                    recordedBy = request.form.get("recordedBy")
                    occurrenceRemarks = request.form.get("occurrenceRemarks")
                lifeStage = request.form.get("lifeStage")
                individualCount = request.form.get("individualCount")
                sex = request.form.get("sex")
                # If taxonInt has been changed, update identifiedBy and dateIdentified
                if str(taxonInt) != str(observation.taxonInt):
                    identifiedBy = request.form.get("identifiedBy")
                    dateIdentified = datetime.today().strftime('%Y-%m-%d')
                else:
                    identifiedBy = observation.identifiedBy
                    dateIdentified = date
                # Get observation
                observation_update = Observations.query.filter_by(occurrenceID=occurrence_id).first()
                # Initialize imageFileNames with existing files that are checked to be kept
                imageFileNames = []
                
                # First handle existing files that should be kept
                for file in files:
                    if request.form.get(file) == 'CHECKED':  # Check if checkbox was checked
                        imageFileNames.append(file)
                
                # Then handle new file uploads
                for file in request.files.getlist("files"):
                    if file.filename == '':
                        continue  # Skip if no file selected
                        
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filename2 = f'{taxonInt}_{filename}'
                        
                        if filename2 in os.listdir(f"{dir_path}/observations/"):
                            flash(f'Image already exists under the filename {filename2}', category="error")
                            return redirect(request.url)
                            
                        try:
                            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2))
                            shutil.copyfile(f"{app.config['UPLOAD_FOLDER']}/{filename2}", 
                                        f"{dir_path}/observations/{filename2}")
                            compress_image(os.path.join(app.config['UPLOAD_FOLDER'], filename2), 
                                        f"{dir_path}/compressed/{filename2}", 20)
                            os.remove(f"{app.config['UPLOAD_FOLDER']}/{filename2}")
                            imageFileNames.append(filename2)
                        except Exception as e:
                            app.logger.error(f"Error processing image {filename2}: {str(e)}")
                            flash(f'Error processing image {filename2}', category="error")
                            continue
                
                # Delete unchecked images
                for file in files:
                    if request.form.get(file) != 'CHECKED':  # Only delete if not checked
                        try:
                            os.remove(f'{dir_path}/compressed/{file}')
                            os.remove(f'{dir_path}/observations/{file}')
                        except Exception as e:
                            app.logger.error(f"Error deleting image {file}: {str(e)}")
                            flash(f'Error deleting image {file}', category="error")
                
                # Join list of image filenames to string
                imageFileNames = ' | '.join(imageFileNames)

                # Update record
                observation_update.taxonInt = taxonInt
                observation_update.decimalLatitude = decimalLatitude
                observation_update.decimalLongitude = decimalLongitude
                observation_update.coordinateUncertaintyInMeters = coordinateUncertaintyInMeters
                observation_update.eventDateTime = eventDateTime
                observation_update.dateIdentified = dateIdentified
                observation_update.identifiedBy = identifiedBy
                observation_update.countryCode = countryCode
                observation_update.county = county
                observation_update.municipality = municipality
                observation_update.locality = locality
                observation_update.recordedBy = recordedBy
                observation_update.lifeStage = lifeStage
                observation_update.individualCount = individualCount
                observation_update.sex = sex
                observation_update.occurrenceRemarks = occurrenceRemarks
                observation_update.imageFileNames = imageFileNames
                observation_update.eventID = event_id
                db.session.commit()
                flash(f'Observation updated!', category="success")
                # Go back to original page
                return redirect(url_for('observations.observation_view', occurrence_id=occurrence_id))
        else:
            return render_template("observation_edit.html", user=current_user, title=title, entomologists=entomologists, taxa=taxa, countries=countries, observation=observation, date=date, time=time, files=files, events=events)
    except Exception as e:
        # Log the error for debugging
        app.logger.error(f"Error editing observation {occurrence_id}: {str(e)}")
        flash('An error occurred while processing your request', category="error")
        return redirect(url_for('observations.observation_filter'))


#####
# Query database for observation-data and return an overview of a single observation
#####
@observations.route('/observation_view/<string:occurrence_id>/', methods=['GET'])
@login_required
def observation_view(occurrence_id):
    title = "Observation page"
    # Query Occurrence data
    occurrence = Observations.query.filter_by(occurrenceID=occurrence_id)\
            .join(Country_codes, Observations.countryCode==Country_codes.countryCode, isouter=True)\
            .join(Taxa, Observations.taxonInt==Taxa.taxonInt, isouter=True)\
            .with_entities(Observations.occurrenceID, Observations.imageFileNames, Observations.eventDateTime, Observations.decimalLatitude, Observations.decimalLongitude, Observations.coordinateUncertaintyInMeters, Country_codes.country, Observations.county, Observations.municipality, Observations.locality, Taxa.taxonID, Taxa.taxonRank, Taxa.scientificName, Taxa.family, Taxa.order, Taxa.cl, Observations.individualCount, Observations.lifeStage, Observations.sex, Observations.recordedBy, Observations.identifiedBy, Observations.dateIdentified, Observations.occurrenceRemarks, Observations.eventID)\
            .first()
    
    files = occurrence.imageFileNames.split(" | ")
    
    return render_template("observation_view.html", title=title, user=current_user, occurrence=occurrence, files = files)

#####
# Filter observations
#####
@observations.route('/observation_filter', methods=['POST', 'GET'])
@login_required
def observation_filter():
    title = "observations"

    # Create  list of names and ranks for taxa-dropdown-select-search bar
    taxa = Taxa.query.join(Observations, Taxa.taxonInt==Observations.taxonInt).all() # Database query for taxa
    ranks = np.unique([i.taxonRank for i in taxa if i.taxonRank]) # Database query for taxon ranks
    cl = tuple(np.unique([i.cl for i in taxa if i.cl]))
    order = tuple(np.unique([i.order for i in taxa if i.order]))
    family = tuple(np.unique([i.family for i in taxa if i.family]))
    genus = tuple(np.unique([i.genus for i in taxa if i.genus]))
    scientificName = tuple(np.unique([i.scientificName for i in taxa]))
    dropdown_names = cl+order+family+genus+scientificName
    dropdown_ranks = tuple(len(cl)*["class"]+len(order)*["order"]+len(family)*["family"]+len(genus)*[
                           "genus"]+len(scientificName)*["scientificName"])

    
    # Get all distinct values for filter dropdowns
    countries = Observations.query.join(Country_codes, Observations.countryCode==Country_codes.countryCode, isouter=True).with_entities(Country_codes.country).distinct().all()
    counties = Observations.query.with_entities(Observations.county).distinct().all()
    municipalities = Observations.query.with_entities(Observations.municipality).distinct().all()
    life_stages = Observations.query.with_entities(Observations.lifeStage).distinct().all()
    sexes = Observations.query.with_entities(Observations.sex).distinct().all()
    recorders = Observations.query.with_entities(Observations.recordedBy).distinct().all()
    
    # Initialize filter variables from request
    taxon_name = request.args.get('taxon_name', '')
    if taxon_name:
        tax_name = taxon_name.split(" [")[0]
        tax_rank = taxon_name.split(" [")[1][:-1]
    else:
        tax_name = ""
        tax_rank = ""

    filters = {
        'start_date': request.args.get('start_date', ''),
        'end_date': request.args.get('end_date', ''),
        'country': request.args.get('country', ''),
        'county': request.args.get('county', ''),
        'municipality': request.args.get('municipality', ''),
        'life_stage': request.args.get('life_stage', ''),
        'sex': request.args.get('sex', ''),
        'rank': request.args.get('taxon_rank', ''),
        'taxon_name': tax_name,
        'recorded_by': request.args.get('recorded_by', '')
    }
    
    # Build the query with filters
    query = Observations.query.join(Country_codes, Observations.countryCode==Country_codes.countryCode, isouter=True)\
            .join(Taxa, Observations.taxonInt==Taxa.taxonInt, isouter=True)
    
    # ScientificName filter

    # Date filter
    if filters['start_date']:
        try:
            start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d')
            query = query.filter(Observations.eventDateTime >= start_date.strftime('%Y-%m-%d'))
        except ValueError:
            pass
            
    if filters['end_date']:
        try:
            end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d')
            query = query.filter(Observations.eventDateTime <= end_date.strftime('%Y-%m-%d'))
        except ValueError:
            pass
    
    # Other filters
    if filters['country']:
        query = query.filter(Country_codes.country == filters['country'])
    
    if filters['county']:
        query = query.filter(Observations.county == filters['county'])
    
    if filters['municipality']:
        query = query.filter(Observations.municipality == filters['municipality'])
    
    if filters['life_stage']:
        query = query.filter(Observations.lifeStage == filters['life_stage'])
    
    if filters['sex']:
        query = query.filter(Observations.sex == filters['sex'])
    
    if filters['recorded_by']:
        query = query.filter(Observations.recordedBy == filters['recorded_by'])
    
    if filters['rank']:
        query = query.filter(Taxa.taxonRank == filters['rank'])

    if filters['taxon_name']:
        if tax_rank == "scientificName":
            query = query.filter(Taxa.scientificName == filters['taxon_name'])
        if tax_rank == "genus":
            query = query.filter(Taxa.genus == filters['taxon_name'])
        if tax_rank == "family":
            query = query.filter(Taxa.family == filters['taxon_name'])
        if tax_rank == "order":
            query = query.filter(Taxa.order == filters['taxon_name'])
        if tax_rank == "class":
            query = query.filter(Taxa.cl == filters['taxon_name'])
        
    # Execute the query
    observations = query.order_by(Observations.eventDateTime.desc())\
    .with_entities(Observations.occurrenceID, Observations.imageFileNames, Observations.eventDateTime, Observations.decimalLatitude, Observations.decimalLongitude, Observations.coordinateUncertaintyInMeters, Country_codes.country, Observations.county, Observations.municipality, Observations.locality, Taxa.taxonID, Taxa.taxonRank, Taxa.scientificName, Taxa.genus, Taxa.family, Taxa.order, Taxa.cl, Observations.individualCount, Observations.lifeStage, Observations.sex, Observations.recordedBy, Observations.occurrenceRemarks)\
    .all()

    # Create statistics
    # 1. Occurrences
    # Create dataframe
    family = []
    order = []
    genus = []
    taxonRank = []
    eventDateTime = []
    for row in observations:
        family.append(row.family)
        order.append(row.order)
        genus.append(row.genus)
        taxonRank.append(row.taxonRank)
        eventDateTime.append(row.eventDateTime)
    occurrences_dict = {"family":family, "order":order, "genus":genus, "taxonRank":taxonRank, "date":eventDateTime}
    occurrences_df = pd.DataFrame(occurrences_dict)
    # Yearly
    occurrence_year = bar_plot_dict(occurrences_df, "year", 0)
    # Monthly
    occurrence_month = bar_plot_dict(occurrences_df, "month", 0)
    # Order
    occurrence_order = bar_plot_dict(occurrences_df, "order", 1)
    # Family
    occurrence_family = bar_plot_dict(occurrences_df, "family", 2)
    # Genus
    occurrence_genus = bar_plot_dict(occurrences_df, "genus", 0.5)
    # Rank
    occurrence_taxonRank = bar_plot_dict(occurrences_df, "taxonRank", 2)
    # Count length
    occ_len = len(observations)

    # 2. Taxa
    # Create dataframe
    scientificName = []
    taxonRank = []
    eventDateTime = []
    order = []
    family = []
    index = 1
    for i in observations:
        if i.scientificName not in scientificName:
            index+=1
            scientificName.append(i.scientificName)
            taxonRank.append(i.taxonRank)
            order.append(i.order)
            family.append(i.family)
            eventDateTime.append(i.eventDateTime)
    taxa_dict = {"scientificName":scientificName, "order":order, "family":family, "taxonRank":taxonRank, "date":eventDateTime}
    
    taxa_df = pd.DataFrame(taxa_dict)
    # Yearly
    taxa_year = bar_plot_dict(taxa_df, "year", 0)
    # Order
    taxa_order = bar_plot_dict(taxa_df, "order", 1)
    # Family
    taxa_family = bar_plot_dict(taxa_df, "family", 0.5)
    # Rank
    taxa_taxonRank = bar_plot_dict(taxa_df, "taxonRank", 1)
    # Count length
    taxa_len = len(taxa_df)
    
    return render_template(
        "observation_filter.html", 
        user=current_user, 
        title=title,
        observations=observations,
        filters=filters,
        dropdown_names=dropdown_names,
        dropdown_ranks=dropdown_ranks,
        ranks=ranks,
        occurrence_year=occurrence_year, # Stats
        occurrence_month=occurrence_month,
        occurrence_order=occurrence_order,
        occurrence_family=occurrence_family,
        occurrence_genus=occurrence_genus,
        occurrence_taxonRank=occurrence_taxonRank,
        occ_len=occ_len,
        taxa_year=taxa_year,
        taxa_order=taxa_order,
        taxa_family=taxa_family,
        taxa_taxonRank=taxa_taxonRank,
        taxa_len=taxa_len,
        countries=[c[0] for c in countries if c[0]],
        counties=[c[0] for c in counties if c[0]],
        municipalities=[m[0] for m in municipalities if m[0]],
        life_stages=[ls[0] for ls in life_stages if ls[0]],
        sexes=[s[0] for s in sexes if s[0]],
        recorders=[r[0] for r in recorders if r[0]]
    )

@observations.route('/filter_by_area', methods=['POST'])
@login_required
def filter_by_area():
    title = "observations"
    # Get observation IDs from the form
    observation_ids = request.form.get('observation_ids', '').split(',')
    
    # Filter observations by these IDs
    observations = Observations.query\
        .join(Country_codes, Observations.countryCode==Country_codes.countryCode, isouter=True)\
        .join(Taxa, Observations.taxonInt==Taxa.taxonInt, isouter=True)\
        .filter(Observations.occurrenceID.in_(observation_ids))\
        .order_by(Observations.eventDateTime.desc())\
        .with_entities(
            Observations.occurrenceID, 
            Observations.imageFileNames, 
            Observations.eventDateTime, 
            Observations.decimalLatitude, 
            Observations.decimalLongitude, 
            Observations.coordinateUncertaintyInMeters, 
            Country_codes.country, 
            Observations.county, 
            Observations.municipality, 
            Observations.locality, 
            Taxa.taxonID, 
            Taxa.taxonRank, 
            Taxa.scientificName, 
            Taxa.genus, 
            Taxa.family, 
            Taxa.order, 
            Taxa.cl, 
            Observations.individualCount, 
            Observations.lifeStage, 
            Observations.sex, 
            Observations.recordedBy, 
            Observations.occurrenceRemarks
        )\
        .all()

    # Create  list of names and ranks for taxa-dropdown-select-search bar
    taxa = Taxa.query.join(Observations, Taxa.taxonInt==Observations.taxonInt).all() # Database query for taxa
    ranks = np.unique([i.taxonRank for i in taxa if i.taxonRank]) # Database query for taxon ranks
    cl = tuple(np.unique([i.cl for i in taxa if i.cl]))
    order = tuple(np.unique([i.order for i in taxa if i.order]))
    family = tuple(np.unique([i.family for i in taxa if i.family]))
    genus = tuple(np.unique([i.genus for i in taxa if i.genus]))
    scientificName = tuple(np.unique([i.scientificName for i in taxa]))
    dropdown_names = cl+order+family+genus+scientificName
    dropdown_ranks = tuple(len(cl)*["class"]+len(order)*["order"]+len(family)*["family"]+len(genus)*[
                           "genus"]+len(scientificName)*["scientificName"])

    
    # Get all distinct values for filter dropdowns
    countries = Observations.query.join(Country_codes, Observations.countryCode==Country_codes.countryCode, isouter=True).with_entities(Country_codes.country).distinct().all()
    counties = Observations.query.with_entities(Observations.county).distinct().all()
    municipalities = Observations.query.with_entities(Observations.municipality).distinct().all()
    life_stages = Observations.query.with_entities(Observations.lifeStage).distinct().all()
    sexes = Observations.query.with_entities(Observations.sex).distinct().all()
    recorders = Observations.query.with_entities(Observations.recordedBy).distinct().all()
    
    filters = {
        'start_date': '',
        'end_date': '',
        'country': '',
        'county': '',
        'municipality': '',
        'life_stage': '',
        'sex': '',
        'rank': '',
        'taxon_name': '',
        'recorded_by': ''
    }

    # Create statistics
    # 1. Occurrences
    # Create dataframe
    family = []
    order = []
    genus = []
    taxonRank = []
    eventDateTime = []
    for row in observations:
        family.append(row.family)
        order.append(row.order)
        genus.append(row.genus)
        taxonRank.append(row.taxonRank)
        eventDateTime.append(row.eventDateTime)
    occurrences_dict = {"family":family, "order":order, "genus":genus, "taxonRank":taxonRank, "date":eventDateTime}
    occurrences_df = pd.DataFrame(occurrences_dict)
    # Yearly
    occurrence_year = bar_plot_dict(occurrences_df, "year", 0)
    # Monthly
    occurrence_month = bar_plot_dict(occurrences_df, "month", 0)
    # Order
    occurrence_order = bar_plot_dict(occurrences_df, "order", 1)
    # Family
    occurrence_family = bar_plot_dict(occurrences_df, "family", 2)
    # Genus
    occurrence_genus = bar_plot_dict(occurrences_df, "genus", 0.5)
    # Rank
    occurrence_taxonRank = bar_plot_dict(occurrences_df, "taxonRank", 2)
    # Count length
    occ_len = len(observations)

    # 2. Taxa
    # Create dataframe
    scientificName = []
    taxonRank = []
    eventDateTime = []
    order = []
    family = []
    index = 1
    for i in observations:
        if i.scientificName not in scientificName:
            index+=1
            scientificName.append(i.scientificName)
            taxonRank.append(i.taxonRank)
            order.append(i.order)
            family.append(i.family)
            eventDateTime.append(i.eventDateTime)
    taxa_dict = {"scientificName":scientificName, "order":order, "family":family, "taxonRank":taxonRank, "date":eventDateTime}
    
    taxa_df = pd.DataFrame(taxa_dict)
    # Yearly
    taxa_year = bar_plot_dict(taxa_df, "year", 0)
    # Order
    taxa_order = bar_plot_dict(taxa_df, "order", 1)
    # Family
    taxa_family = bar_plot_dict(taxa_df, "family", 0.5)
    # Rank
    taxa_taxonRank = bar_plot_dict(taxa_df, "taxonRank", 1)
    # Count length
    taxa_len = len(taxa_df)
    
    return render_template(
        "observation_filter.html", 
        user=current_user, 
        title=title,
        observations=observations,
        filters=filters,
        dropdown_names=dropdown_names,
        dropdown_ranks=dropdown_ranks,
        ranks=ranks,
        occurrence_year=occurrence_year, # Stats
        occurrence_month=occurrence_month,
        occurrence_order=occurrence_order,
        occurrence_family=occurrence_family,
        occurrence_genus=occurrence_genus,
        occurrence_taxonRank=occurrence_taxonRank,
        occ_len=occ_len,
        taxa_year=taxa_year,
        taxa_order=taxa_order,
        taxa_family=taxa_family,
        taxa_taxonRank=taxa_taxonRank,
        taxa_len=taxa_len,
        countries=[c[0] for c in countries if c[0]],
        counties=[c[0] for c in counties if c[0]],
        municipalities=[m[0] for m in municipalities if m[0]],
        life_stages=[ls[0] for ls in life_stages if ls[0]],
        sexes=[s[0] for s in sexes if s[0]],
        recorders=[r[0] for r in recorders if r[0]]
    )