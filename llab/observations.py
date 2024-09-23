# load packages
from .functions import bar_plot_dict
from flask import Blueprint, current_app, request, redirect, url_for, render_template, flash, request
from flask_login import login_required, current_user
from .models import User, Collectors, Taxa, Country_codes, Observations
from . import db
from .functions import compress_image
import datetime
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