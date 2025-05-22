# load packages
from .functions import bar_plot_dict
from flask import Blueprint, current_app, request, redirect, url_for, render_template, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from datetime import datetime
from .models import User, Collectors, Taxa, Country_codes, Observations
from . import db
from .functions import compress_image
import uuid
import os
import numpy as np
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

# Add determinations to database. Add specimens to database if not already present.
@observations.route('/observation_add', methods=["POST", "GET"])
@login_required
def observation_add():
    # Path to image directory
    dir_path = "/var/www/llab/llab/static/images"
    # Get researchers
    entomologists = Collectors.query.all()
    # Get taxon data
    taxa = Taxa.query.all()
    # Get Country codes
    countries = Country_codes.query.all()
    # POST
    if request.method == 'POST':
            occurrenceID=str(uuid.uuid4())
            taxonInt =  request.form.get("taxonInt")
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
            lifeStage = request.form.get("lifeStage")
            individualCount = request.form.get("individualCount")
            sex = request.form.get("sex")
            occurrenceRemarks = request.form.get("occurrenceRemarks")
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
                 countryCode = countryCode,
                 county = county,
                 municipality = municipality,
                 locality = locality,
                 recordedBy = recordedBy,
                 lifeStage = lifeStage,
                 individualCount = individualCount,
                 sex = sex,
                 occurrenceRemarks = occurrenceRemarks,
                 createdByUserID=current_user.id)
            # Add new objects to database
            db.session.add(new_observation)
            # Commit
            db.session.commit()
            flash('Illustration added', category="success")
            return redirect(url_for("observations.observation_add")) 
    return render_template("observation_add.html", user=current_user, entomologists=entomologists, taxa=taxa, countries=countries)

#####
# Query database for observation-data and return an overview of a single observation
@observations.route('/observation_view/<string:occurrence_id>/', methods=['GET'])
@login_required
def observation_view(occurrence_id):
    title = "Observation page"
    # Query Occurrence data
    occurrence = Observations.query.filter_by(occurrenceID=occurrence_id)\
            .join(Country_codes, Observations.countryCode==Country_codes.countryCode, isouter=True)\
            .join(Taxa, Observations.taxonInt==Taxa.taxonInt, isouter=True)\
            .with_entities(Observations.occurrenceID, Observations.imageFileNames, Observations.eventDateTime, Observations.decimalLatitude, Observations.decimalLongitude, Observations.coordinateUncertaintyInMeters, Country_codes.country, Observations.county, Observations.municipality, Observations.locality, Taxa.taxonID, Taxa.taxonRank, Taxa.scientificName, Taxa.family, Taxa.order, Taxa.cl, Observations.individualCount, Observations.lifeStage, Observations.sex, Observations.recordedBy, Observations.occurrenceRemarks)\
            .first()
    
    files = occurrence.imageFileNames.split(" | ")
    
    return render_template("observation_view.html", title=title, user=current_user, occurrence=occurrence, files = files)

#####
# Filter observations
@observations.route('/observation_filter', methods=['POST', 'GET'])
@login_required
def observation_filter():
    title = "Filter observations"

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
    .with_entities(Observations.occurrenceID, Observations.imageFileNames, Observations.eventDateTime, Observations.decimalLatitude, Observations.decimalLongitude, Observations.coordinateUncertaintyInMeters, Country_codes.country, Observations.county, Observations.municipality, Observations.locality, Taxa.taxonID, Taxa.taxonRank, Taxa.scientificName, Taxa.family, Taxa.order, Taxa.cl, Observations.individualCount, Observations.lifeStage, Observations.sex, Observations.recordedBy, Observations.occurrenceRemarks)\
    .all()
    
    return render_template(
        "observation_filter.html", 
        user=current_user, 
        title=title,
        observations=observations,
        filters=filters,
        dropdown_names=dropdown_names,
        dropdown_ranks=dropdown_ranks,
        ranks=ranks,
        countries=[c[0] for c in countries if c[0]],
        counties=[c[0] for c in counties if c[0]],
        municipalities=[m[0] for m in municipalities if m[0]],
        life_stages=[ls[0] for ls in life_stages if ls[0]],
        sexes=[s[0] for s in sexes if s[0]],
        recorders=[r[0] for r in recorders if r[0]]
    )