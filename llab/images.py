from flask import Blueprint, current_app, flash, request, redirect, url_for, render_template, send_from_directory
from flask_login import login_required, current_user
from .models import User, Collecting_events, Event_images, Occurrences, Occurrence_images, Illustrations, Taxa
from . import db
import os
import shutil
import glob
from werkzeug.utils import secure_filename

# connect to __init__ file
images = Blueprint('images', __name__)

# Specify app
app = current_app

# Specify allowed file extensions and define a function to control that input file is alowed
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Specify image categories
imagecat = ['habitat', 'trap', 'substrate', 'colony', 'behaviour', 'other']
imagecat2 = ['lateral', 'ventral', 'dorsal', 'anterior', 'face', 'fore-wing', 'hind-wing', 'propodeum', 'label', 'in-situ']
licenses = ["All-rights-served", "Public-domain", "CC-by-4", "CC-by-2", "CC-by-sa-2", "CC-by-nc-2", "CC-by-nd-2", "CC-by-nc-nd-2"]
id_qualifier = ["", "?", "cf", "aff", "agg"]
type_status = ["", "holotype", "paratype", "lectotype", "neotype", "syntype"]
sexes = ["", "female", "male"]
lifestage = ["adult", "larva", "pupa"]
imagetype = ["photo", "drawing"]

@images.route('/event_image', methods=['GET', 'POST'])
@login_required
def event_image():
    title = "Collecting event images"
    dir_path = "/var/www/llab/llab/static/images/events"
    # Get image names starting with user initials
    files = [os.path.basename(x) for x in glob.glob(f"{dir_path}/{current_user.initials}*")]
    if request.method == 'POST':
        # Button 1: move images to image-folder and populate database
        if request.form.get('action1') == 'VALUE1':
            # Request form input
            eventID = request.form.get("eventID")
            imageCategory = request.form.get("imageCategory")
            comment = request.form.get("comment")
            # For each file in post request
            for file in request.files.getlist("files"):
                # If the user does not select a file
                if file.filename == '':
                    flash('No selected file', category="error")
                    return redirect(request.url)
                # Secure the filenames and save 
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename2 = f'{eventID}_{filename}'
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2)) # Save file to upload folder
                    shutil.copyfile(f"{app.config['UPLOAD_FOLDER']}/{filename2}", f"{dir_path}/{filename2}") # Move file to image-folder
                    os.remove(f"{app.config['UPLOAD_FOLDER']}/{filename2}") # Remove file from upload-folder
                    # New Print_events object
                    new_event_image = Event_images(
                        filename=filename2, imageCategory=imageCategory, comment=comment, eventID=eventID, createdByUserID=current_user.id)
                    # Add new objects to database
                    db.session.add(new_event_image)
                    # Commit
                    db.session.commit()
            flash('Collecting-event images added', category="success")
            return redirect(url_for("images.event_image"))
    # Query collecting events
    events = Collecting_events.query.filter_by(
        createdByUserID=current_user.id).order_by(Collecting_events.eventID.desc())
    return render_template("event_image.html", title=title, user=current_user, files=files, events=events, imagecat=imagecat)

@images.route('/specimen_image', methods=['GET', 'POST'])
@login_required
def specimen_image():
    title = "Specimen images"
    dir_path = "/var/www/llab/llab/static/images/specimens"
    # Get image names starting with user initials
    if request.method == 'POST':
        # Request form input
        occurrence = request.form.get("occurrenceID")
        imageCategory = request.form.get("imageCategory")
        comment = request.form.get("comment")
        # Button 1:
        if request.form.get('action1') == 'VALUE1':
            # check if the occurrenceID exists
            if Occurrences.query.filter_by(occurrenceID=occurrence).first() is None:
                flash('occurrenceID does not exist in database', category="error")
                return redirect(request.url)
            # For each file in post request
            for file in request.files.getlist("files"):
                # If the user does not select a file
                if file.filename == '':
                    flash('No selected file', category="error")
                    return redirect(request.url)
                # Secure the filenames and save 
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename2 = f'{occurrence}_{filename}'
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2)) # Save file to upload folder
                    shutil.copyfile(f"{app.config['UPLOAD_FOLDER']}/{filename2}", f"{dir_path}/{filename2}") # Move file to image-folder
                    os.remove(f"{app.config['UPLOAD_FOLDER']}/{filename2}") # Remove file from upload-folder
                    # New Print_events object
                    new_specimen_image = Occurrence_images(
                        filename=filename2, imageCategory=imageCategory, comment=comment, occurrenceID=occurrence, createdByUserID=current_user.id)
                    # Add new objects to database
                    db.session.add(new_specimen_image)
                    # Commit
                    db.session.commit()
            flash('Specimen images added', category="success")
            return redirect(url_for("images.specimen_image"))

    return render_template("specimen_image.html", title=title, user=current_user, imagecat=imagecat2)

@images.route('/add_illustrations', methods=['GET', 'POST'])
@login_required
def add_illustrations():
    title = "Add illustrations"
    dir_path = "/var/www/llab/llab/static/images/illustrations"
    last_values = None
    # Get taxon data
    taxa = Taxa.query.all()
    # POST
    if request.method == 'POST':
        # Button 3: Clear values
        if request.form.get('clear_files') == 'VALUE3':
            return redirect(url_for("images.add_illustrations")) 
        # Button 2: Copy input values from previous record
        if request.form.get('action2') == 'VALUE2':
            last_values = Illustrations.query.order_by(Illustrations.id.desc()).first()
        # Button 1: submit new record
        if request.form.get('action1') == 'VALUE1':
            # Request form input
            imageType = request.form.get("imageType")
            category = request.form.get("category")
            scientificName = request.form.get("scientificName")
            sex = request.form.get("sex")
            lifeStage = request.form.get("lifeStage")
            rightsHolder = request.form.get("rightsHolder")
            license = request.form.get("license")
            associatedReference = request.form.get("associatedReference")
            remarks = request.form.get("remarks")
            identificationQualifier = request.form.get("identificationQualifier")
            identifiedBy = request.form.get("identifiedBy")
            typeStatus = request.form.get("typeStatus")
            typeID = request.form.get("typeID")
            ownerInstitutionCode = request.form.get("ownerInstitutionCode")
            # For each file in post request
            for file in request.files.getlist("files"):
                # If the user does not select a file
                if file.filename == '':
                    flash('No selected file', category="error")
                    return redirect(request.url)
                # Secure the filenames and save 
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename2 = f'{scientificName.split(" ")[0]}_{scientificName.split(" ")[1]}_{sex}_{category}_{filename}'
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2)) # Save file to upload folder
                    shutil.copyfile(f"{app.config['UPLOAD_FOLDER']}/{filename2}", f"{dir_path}/{filename2}") # Move file to image-folder
                    os.remove(f"{app.config['UPLOAD_FOLDER']}/{filename2}") # Remove file from upload-folder
                    # New Print_events object
                    new_illustration = Illustrations(
                        filename = filename2,
                        imageType = imageType,
                        category = category,
                        scientificName = scientificName,
                        sex = sex,
                        lifeStage = lifeStage,
                        rightsHolder = rightsHolder,
                        license = license,
                        associatedReference = associatedReference,
                        remarks = remarks,
                        identificationQualifier = identificationQualifier,
                        identifiedBy = identifiedBy,
                        typeStatus = typeStatus,
                        typeID = typeID,
                        ownerInstitutionCode = ownerInstitutionCode,
                        createdByUserID=current_user.id
                    )
                    # Add new objects to database
                    db.session.add(new_illustration)
                    # Commit
                    db.session.commit()
            flash('Illustration added', category="success")
            return redirect(url_for("images.add_illustrations")) 
    return render_template("illustrations.html", title=title, user=current_user, imagecat = imagecat2, licenses=licenses, id_qualifier=id_qualifier, type_status=type_status, sexes=sexes, lifestage=lifestage, imagetype=imagetype, last_values=last_values, taxa=taxa)