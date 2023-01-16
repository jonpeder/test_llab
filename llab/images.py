from flask import Blueprint, current_app, flash, request, redirect, url_for, render_template, send_from_directory
from flask_login import login_required, current_user
from .models import User, Collecting_events, Event_images, Occurrences, Occurrence_images
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

# Specify image categories
imagecat2 = ['habitus', 'in-situ', 'lateral', 'ventral', 'dorsal', 'face', 'fore-wing', 'hind-wing']


@images.route('/event_image', methods=['GET', 'POST'])
@login_required
def event_image():
    title = "Collecting event images"
    dir_path = os.path.join(app.config['UPLOAD_FOLDER'], "event")
    dir_path2 = "/var/www/llab/llab/static/images"
    # Get image names starting with user initials
    files = [os.path.basename(x) for x in glob.glob(f"{dir_path}/{current_user.initials}*")]
    if request.method == 'POST':
        # Request form input
        eventID = request.form.get("eventID")
        imageCategory = request.form.get("imageCategory")
        comment = request.form.get("comment")

        # Button 1: Add file to upload folder. Tempararily view the files before adding to database.
        if request.form.get('action1') == 'VALUE1':
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part', category="error")
                return redirect(request.url)
            file = request.files['file']
            # If the user does not select a file, the browser submits an empty file without a filename.
            if file.filename == '':
                flash('No selected file', category="error")
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(dir_path, f'{eventID}_{filename}'))
                return redirect(url_for("images.event_image"))

        # Button 2: Delete files in upload folder
        if request.form.get('action2') == 'VALUE2':
            # Find and delete filenames starting with user initials
            for i in files:
                os.remove(f"{dir_path}/{i}")
            return redirect(url_for("images.event_image"))

        # Button 3: move images to image-folder and populate database
        if request.form.get('action3') == 'VALUE3':
            for i in files:
                shutil.copyfile(f"{dir_path}/{i}", f"{dir_path2}/{i}")
                os.remove(f"{dir_path}/{i}")
                # New Print_events object
                new_event_image = Event_images(
                    filename=i, imageCategory=imageCategory, comment=comment, eventID=eventID, createdByUserID=current_user.id)
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


@images.route('/test_images', methods=['GET', 'POST'])
@login_required
def test_images():
    title="Test image"
    return render_template("test_images.html", title=title, user=current_user)


@images.route('/specimen_image', methods=['GET', 'POST'])
@login_required
def specimen_image():
    title = "Specimen images"
    dir_path = "/var/www/llab/llab/static/uploads/specimen"
    # Get image names starting with user initials
    if request.method == 'POST':
        # Request form input
        occurrence = request.form.get("occurrenceID")
        imageCategory = request.form.get("imageCategory")
        comment = request.form.get("comment")
        print("1")
        # Button 1:
        if request.form.get('action1') == 'VALUE1':
            # check if the occurrenceID exists
            if Occurrences.query.filter_by(occurrenceID=occurrence).first() is None:
                flash('occurrenceID does not exist in database', category="error")
                return redirect(request.url)
            # For each file in post request
            for file in request.files.getlist("file"):
                # If the user does not select a file
                if file.filename == '':
                    flash('No selected file', category="error")
                    return redirect(request.url)
                # Secure the filenames and save 
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename2 = f'{occurrence}_{filename}'
                    file.save(os.path.join(dir_path, filename2)) # Save file to upload folder
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

