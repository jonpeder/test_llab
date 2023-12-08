from flask import Blueprint, current_app, flash, request, redirect, url_for, render_template
from flask_login import login_required, current_user
from .models import User, Occurrence_images, Landmarks, Landmark_datasets
from . import db
#import os
#import numpy as np
#from werkzeug.utils import secure_filename

# connect to __init__ file
landmarks = Blueprint('landmarks', __name__)

# Specify app
app = current_app

### FUNCTIONS

# Function for selecting next image and landmark specified in dataset
def select_next_image(datasetName, filename = None, landmark = None):
    dataset = Landmark_datasets.query.filter_by(datasetName=datasetName).first()
    image_ids = "".join(dataset.imageIDs).split(" | ")
    occurrence_images = Occurrence_images.query.filter(Occurrence_images.id.in_(image_ids)).all()
    filenames = [i.filename for i in occurrence_images]
    landmarks = "".join(dataset.landmarks).split(", ")
    if filename is None:
        next_image = filenames[0]
        next_landmark = landmarks[0]
        index = 0
    else:
        index = 0
        for f in filenames:
            index += 1
            if f == filename:
                if index == len(filenames):
                    next_image = filenames[0]
                    index2 = 0
                    for lm in landmarks:
                        index2 += 1
                        if lm == landmark:
                            if index2 == len(landmarks):
                                next_landmark = None
                            else:
                                next_landmark = landmarks[index2]
                else:
                    next_image = filenames[index]
                    next_landmark = landmark
                break
    if next_landmark is None:
        return redirect(url_for("landmarks.landmark_dataset"))
    else:
        image_index = index + 1
        return redirect(url_for("landmarks.landmark_image", datasetName=datasetName, filename=next_image, landmark=next_landmark, image_index = image_index))

# coordinates are sent as slightly weird URL parameters (e.g. 0.png?214,243)
# parse them, will crash server if they are coming in unexpected format
def parse_coordinates(args):
    keys = list(args.keys())
    assert len(keys) == 1
    coordinates = keys[0]

    assert len(coordinates.split(",")) == 2
    x, y = coordinates.split(",")
    x = int(x)
    y = int(y)
    return x, y


### ROUTES

# Add landmark-dataset
@landmarks.route('/landmark_add_dataset/<taxa>/<image_category>/<image_ids>', methods=['GET', 'POST'])
@login_required
def landmark_add_dataset(taxa, image_category, image_ids):
    title = "Create landmarks dataset"
    if request.method == 'POST':
        datasetName = request.form.get("datasetName")
        landmarks = request.form.get("landmarks")
        # Add to database
        new_landmarks_dataset = Landmark_datasets(datasetName=datasetName, landmarks=landmarks, taxa=taxa, imageCategory=image_category,
                                        imageIDs=image_ids,  createdByUserID=current_user.id)
        # Add new objects to database
        db.session.add(new_landmarks_dataset)
        # Commit
        db.session.commit()
        flash(f'The dataset {datasetName} created!', category="success")
    return render_template("landmark_add_dataset.html", title=title, user=current_user)

# Landmark dataset page
@landmarks.route('/landmark_dataset/', methods=['GET', 'POST'])
@login_required
def landmark_dataset():
    title = 'Landmark-datasets'
    # Query list of landmark-datasets
    datasets = Landmark_datasets.query.all()
    if request.method == 'POST':
        datasetName = request.form.get("datasetName")
        if request.form.get('action1') == 'VALUE1':
            return  select_next_image(datasetName=datasetName)
        else:
            dataset = Landmark_datasets.query.filter_by(datasetName=datasetName).first()
            landmarks = Landmarks.query.filter_by(datasetName=datasetName).all()
            image_ids = "".join(dataset.imageIDs).split(" | ")
            landmark_names = "".join(dataset.landmarks).split(", ")
            occurrence_images = Occurrence_images.query.filter(Occurrence_images.id.in_(image_ids)).with_entities(Occurrence_images.id, Occurrence_images.filename).all()
            if request.form.get('action2') == 'VALUE2':
                return render_template("landmark_dataset.html", title=title, datasets=datasets, user=current_user, landmarks=landmarks, landmark_names=landmark_names, occurrence_images=occurrence_images, datasetName=datasetName, condition="coordinates")
            if request.form.get('action3') == 'VALUE3':
                return render_template("landmark_dataset.html", title=title, datasets=datasets, user=current_user, landmarks=landmarks, landmark_names=landmark_names, occurrence_images=occurrence_images, datasetName=datasetName, condition="images")     
    else:
        return render_template("landmark_dataset.html", title=title, datasets=datasets, user=current_user)

# Send next image to front-end
@landmarks.route('/landmark_image/<datasetName>/<filename>/<string:landmark>/<int:image_index>/', methods=['GET', 'POST'])
@login_required
def landmark_image(datasetName, filename, landmark, image_index):
    title = f'No. <strong>{image_index}</strong> <br>Add landmark: <span style="color: rgb(255, 0, 0)"><strong>{landmark}</strong></span>'
    dir_path = "static/images/compressed"
    return render_template("landmark_images.html", title=title, dir_path=dir_path, datasetName=datasetName, filename=filename, landmark=landmark, user=current_user)

# Add coordinates to database
@landmarks.route('/add_to_database/<datasetName>/<filename>/<landmark>/<int:condition>/')
@login_required
def add_to_database(datasetName, filename, landmark, condition):
    # If image was clicked condition 1
    if condition == 1:
        if len(request.args) == 0:
            return redirect(url_for("landmark_image", datasetName=datasetName, filename=filename, landmark=landmark))
        x, y = parse_coordinates(request.args)
        # Check if combination of image and landmark allready exists
        existing_landmark = Landmarks.query.filter_by(landmark=landmark).filter_by(filename=filename).filter_by(datasetName=datasetName).first()
        # If combination does not exist, create new record
        if existing_landmark is None:
            # Populate database
            new_landmark = Landmarks(landmark=landmark, filename=filename, datasetName=datasetName, xCoordinate=x, yCoordinate=y, createdByUserID=current_user.id)
            # Add new objects to database
            db.session.add(new_landmark)
        # If combination exists, update coordinates
        else:
            existing_landmark.xCoordinate = x
            existing_landmark.yCoordinate = y
            existing_landmark.createdByUserID = current_user.id
        # Commit
        db.session.commit()
    # Return to select next image
    return  select_next_image(datasetName=datasetName, filename=filename, landmark=landmark)
