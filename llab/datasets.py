# Flask module for handling datasets
from flask import Blueprint, request, redirect, url_for, render_template, flash, request, jsonify
from flask_login import login_required, current_user
from .models import User, Datasets
from . import db
import numpy as np
import pandas as pd

# connect to __init__ file
datasets = Blueprint('datasets', __name__)

# Route for adding new dataset
@datasets.route('/dataset_new', methods=['POST', 'GET'])
@login_required
def dataset_new():
    if request.method == 'POST':
        # Get form data
        dataset_name = request.form['dataset_name']
        dataset_description = request.form['dataset_description']
        datasetManager = request.form['datasetManager']
        rightsHolder = request.form['rightsHolder']
        license = request.form['license']
        # Check if dataset already exists
        dataset = Datasets.query.filter_by(datasetName=dataset_name).first()
        if dataset:
            flash('Dataset already exists', 'error')
            return redirect(url_for('datasets.datasets'))
        # Add new dataset to database
        new_dataset = Datasets(datasetName=dataset_name, datasetDescription=dataset_description, datasetManager=datasetManager, rightsHolder=rightsHolder, license=license, createdByUserID=current_user.id)
        db.session.add(new_dataset)
        db.session.commit()
        # Message to user
        flash('Dataset added successfully', 'success')
        # Render datasets page
    return render_template("dataset_new.html", title = "New dataset", user=current_user)

# Add specimens to dataset
@datasets.route('/add_to_dataset', methods=['POST'])
def add_to_dataset():
    if request.json: # Check if data is received
        data = request.json # Get the data
        if data['ids'] == []: # Check if records are selected
            return jsonify({"status": "error", "message": "No records selected"})
        else:
            datasetName = data['datasetName'] # Get the datasetName
            dataset = Datasets.query.filter_by(datasetName=datasetName).first() # Get the dataset
            if dataset.specimenIDs:
                old_dataset = dataset.specimenIDs.split(" | ")
            else:
                old_dataset = []
            new_dataset = np.unique(old_dataset + data['ids']) # Add the new specimenIDs to the dataset
            old_dataset_length = len(old_dataset) # Get the length of the old dataset
            new_dataset_length = len(new_dataset) # Get the length of the new dataset
            added_records = new_dataset_length - old_dataset_length # Get the number of records added
            dataset.specimenIDs = " | ".join(new_dataset)  # Convert the list to a string. Update the dataset
            db.session.commit() # Commit the changes
            # Process the data as needed
            return jsonify({"status": "success", "message": f"{added_records} records added"})
    else:
        return jsonify({"status": "error", "message": "No data received"})

# Remove specimens from dataset
@datasets.route('/remove_from_dataset', methods=['POST'])
def remove_from_dataset():
    if request.json: # Check if data is received
        data = request.json # Get the data
        if data['ids'] == []: # Check if records are selected
            return jsonify({"status": "error", "message": "No records selected"})
        else:
            specimenIDs = data['ids'] # Get the specimenIDs to remove
            datasetName = data['datasetName'] # Get the datasetName
            # Update dataset table with removed records
            dataset = Datasets.query.filter_by(datasetName=datasetName).first() # Get the dataset
            if dataset.specimenIDs:
                old_dataset = dataset.specimenIDs.split(" | ") # Get the old specimenIDs
            else:
                old_dataset = []
            new_dataset = [i for i in old_dataset if i not in specimenIDs] # Remove the specified specimenIDs
            old_dataset_length = len(old_dataset) # Get the length of the old dataset
            new_dataset_length = len(new_dataset) # Get the length of the new dataset
            added_records = old_dataset_length - new_dataset_length # Get the number of records added
            dataset.specimenIDs = " | ".join(new_dataset) # Convert the list to a string. Update the dataset
            db.session.commit() # Commit the changes
            # Process the data as needed
            return jsonify({"status": "success", "message": f"{added_records} records removed"})
    else:
        return jsonify({"status": "error", "message": "No dataset selected"})
