from .functions import new_unit_id
from flask import Blueprint, current_app, flash, request, render_template, redirect, url_for
from flask_login import login_required, current_user
from .models import Taxa, Occurrence_images, Occurrences, Identification_events, Print_det, Illustrations
from . import db
import numpy as np
from werkzeug.utils import secure_filename
import os
from pylibdmtx.pylibdmtx import encode
from PIL import Image
import io

# connect to __init__ file
taxa = Blueprint('taxa', __name__)

# Specify app
app = current_app

# Variables
ranks = ['species', 'species-group', 'genus', 'tribe', 'subfamily',
         'family', 'superfamily', 'infraorder', 'order', 'class', 'spnov', 'other']

# Function to add taxon
@taxa.route('/add_taxon', methods=["POST", "GET"])
@login_required
def add_taxon():
    title = "Add taxon"
    # POST
    if request.method == 'POST':
        # Get input from form
        taxonID = request.form.get("taxonID").strip()
        taxonName = request.form.get("taxonName").strip()
        scientificNameAuthorship = request.form.get("scientificNameAuthorship").strip()
        taxonRank = request.form.get("rank").strip()
        genus = request.form.get("genus").strip()
        family = request.form.get("family").strip()
        order = request.form.get("order").strip()
        publishedIn = request.form.get("publishedIn").strip()
        # Scientific name
        if scientificNameAuthorship is None or scientificNameAuthorship == "":
            scientificName = taxonName
        else:
            scientificName = f'{taxonName} {scientificNameAuthorship}'
        # Specific epithet
        if taxonRank == "species":
            specificEpithet = taxonName.replace(f'{genus} ', "")
        else:
            specificEpithet = ""
        # Add taxon to database
        if request.form.get('action2') == 'VALUE2':
            # Control that scientificName is not already used
            already_existing_taxon = Taxa.query.filter_by(
                scientificName=scientificName).first()
            if already_existing_taxon:
                flash('The taxon does aready exist', category='error')
            elif (taxonName == ""):
                flash('Taxon name cannot be empty!', category='error')
            elif (taxonRank == "species" and scientificNameAuthorship == ""):
                flash('Authorship cannot be empty for a species!', category='error')
            elif (taxonRank == "genus" and scientificNameAuthorship == ""):
                flash('Authorship cannot be empty for a genus!', category='error')
            elif (taxonRank == "species" and genus == "" or taxonRank == "species" and family == "" or taxonRank == "species" and order == ""
                    or taxonRank == "species-group" and genus == "" or taxonRank == "species-group" and family == "" or taxonRank == "species-group" and order == ""
                    or taxonRank == "spnov" and genus == "" or taxonRank == "spnov" and family == "" or taxonRank == "sspnov" and order == "" 
                    or taxonRank == "genus" and family == "" or taxonRank == "genus" and order == "" 
                    or taxonRank == "tribe" and family == "" or taxonRank == "tribe" and order == "" 
                    or taxonRank == "subfamily" and family == "" or taxonRank == "subfamily" and order == "" 
                    or taxonRank == "family" and order == ""
                    or taxonRank == "superfamily" and order == ""
                    or taxonRank == "infraorder" and order == ""):
                flash('Specify parent taxa!', category='error')
            else:
                # Add to database
                new_taxon = Taxa(scientificName=scientificName, taxonRank=taxonRank, scientificNameAuthorship=scientificNameAuthorship, specificEpithet=specificEpithet,
                                 genus=genus, family=family, order=order, cl="Insecta", taxonID=taxonID, createdByUserID=current_user.id, publishedIn=publishedIn)
                # Add new objects to database
                db.session.add(new_taxon)
                # Commit
                db.session.commit()
                flash(f'{scientificName} added!', category="success")

    # Return html-page
    return render_template("taxon_add.html", title=title, user=current_user, ranks=ranks)


# Function to edit/delete taxon
@taxa.route('/edit_taxon', methods=["POST", "GET"])
@login_required
def edit_taxon():
    title = "Edit taxon"
    # Get list of taxa from database
    taxa = Taxa.query.all()
    # Post
    if request.method == 'POST':
        # Button 1: Edit
        if request.form.get('action1') == 'VALUE1':
            # Get input taxon name
            scientificName = request.form.get("scientificName")
            # Get taxon_data from from database
            taxon = Taxa.query.filter_by(scientificName=scientificName).first()
            return render_template("taxon_edit.html", title=title, user=current_user, ranks=ranks, taxa=taxa, taxon=taxon)
        # Button 2: Update
        elif request.form.get('action2') == 'VALUE2':
            # Get input from form
            scientificName_old = request.form.get("scientificName_old")
            taxonID = request.form.get("taxonID")
            taxonName = request.form.get("taxonName")
            scientificNameAuthorship = request.form.get(
                "scientificNameAuthorship")
            taxonRank = request.form.get("rank")
            genus = request.form.get("genus")
            family = request.form.get("family")
            order = request.form.get("order")
            publishedIn = request.form.get("publishedIn")
            # Scientific name
            if scientificNameAuthorship is None or scientificNameAuthorship == "":
                scientificName_new = taxonName
            else:
                scientificName_new = f'{taxonName} {scientificNameAuthorship}'
            # Specific epithet
            if taxonRank == "species":
                specificEpithet = taxonName.replace(f'{genus} ', "")
            else:
                specificEpithet = ""
            # Create condition for the taxon to be updated. The taxon name should not be empty. If rank is species or genus, authorship cannot be empty. Scientific name should not be used in another taxon record.
            if (taxonName == ""):
                update=False
                flash('Taxon name cannot be empty!', category='error')
            elif (taxonRank == "species" and scientificNameAuthorship == ""):
                update=False
                flash('Authorship cannot be empty for a species!', category='error')
            elif (taxonRank == "genus" and scientificNameAuthorship == ""):
                update=False
                flash('Authorship cannot be empty for a genus!', category='error')
            elif (taxonRank == "species" and genus == "" or taxonRank == "species" and family == "" or taxonRank == "species" and order == ""
                    or taxonRank == "species-group" and genus == "" or taxonRank == "species-group" and family == "" or taxonRank == "species-group" and order == ""
                    or taxonRank == "spnov" and genus == "" or taxonRank == "spnov" and family == "" or taxonRank == "sspnov" and order == "" 
                    or taxonRank == "genus" and family == "" or taxonRank == "genus" and order == "" 
                    or taxonRank == "tribe" and family == "" or taxonRank == "tribe" and order == "" 
                    or taxonRank == "subfamily" and family == "" or taxonRank == "subfamily" and order == "" 
                    or taxonRank == "family" and order == ""
                    or taxonRank == "superfamily" and order == ""
                    or taxonRank == "infraorder" and order == ""):
                update=False
                flash('Specify parent taxa!', category='error')
            elif scientificName_old != scientificName_new:
                already_existing_taxon = Taxa.query.filter_by(
                    scientificName=scientificName_new).first()
                if already_existing_taxon:
                    update=False
                    flash('This combination aready exists in another taxon record!', category='error')
                else:
                    update=True
            else:
                update=True
            # Update taxon if condition is true
            if update:
            # Update taxon
                taxon = Taxa.query.filter_by(scientificName=scientificName_old).first()
                taxon.scientificName = scientificName_new.strip()
                taxon.taxonID = taxonID
                taxon.taxonRank = taxonRank
                taxon.scientificNameAuthorship = scientificNameAuthorship
                taxon.specificEpithet = specificEpithet
                taxon.genus = genus
                taxon.family = family
                taxon.order = order
                taxon.publishedIn = publishedIn
                # Update all identification events
                #updated_occ = Occurrences.query.filter_by(scientificName=scientificName_old).update({Occurrences.scientificName : scientificName_new})
                updated_id = Identification_events.query.filter_by(scientificName=scientificName_old).update({Identification_events.scientificName : scientificName_new})
                # Commit
                db.session.commit()
                flash(f'{scientificName_old} updated!', category="success")
            # Get list of taxa from database
            return redirect(url_for('taxa.edit_taxon'))

        # Button 3: Delete
        elif request.form.get('action3') == 'VALUE3':
            scientificName_old = request.form.get("scientificName_old")
            taxon = Taxa.query.filter_by(scientificName=scientificName_old).first()
            db.session.delete(taxon)
            # Delete identification events
            delete_identification_events = Identification_events.query.filter_by(scientificName=scientificName_old).all()
            if delete_identification_events:
                db.session.delete(delete_identification_events)
            # Commit changes
            db.session.commit()
            flash(f'{scientificName_old} deleted!', category="success")
            return redirect(url_for('taxa.edit_taxon'))
        else:
            return redirect(url_for('taxa.edit_taxon'))

    else:
        return render_template("taxon_edit.html", title=title, user=current_user, ranks=ranks, taxa=taxa)


# Function to view images of selected taxa
@taxa.route('/taxon_image', methods=['GET', 'POST'])
@login_required
def taxon_image():
    title = "Taxon images"
    imagecat = ['lateral', 'ventral', 'dorsal', 'anterior', 'face', 'fore-wing', 'hind-wing', 'propodeum', 'label', 'in-situ']
    dir_path = "static/images"
    # Prepare list of taxa for dropdown-select-search bar
    taxa = Taxa.query.all()  # Database query for taxa
    order = tuple(np.unique([i.order for i in taxa if i.order]))
    family = tuple(np.unique([i.family for i in taxa if i.family]))
    genus = tuple(np.unique([i.genus for i in taxa if i.genus]))
    scientificName = tuple(np.unique([i.scientificName for i in taxa]))
    dropdown_names = order+family+genus+scientificName
    dropdown_ranks = tuple(len(order)*["order"]+len(family)*["family"]+len(genus)*[
                           "genus"]+len(scientificName)*["scientificName"])
    # POST
    if request.method == 'POST':
        # Get input
        taxa = request.form.getlist("taxon_name")
        image_categories = request.form.getlist("image_categories")
        # Use all image categories if no image category is selected
        if not image_categories:
            image_categories = imagecat
        # Loop over selected taxa and get scientific names of (children) species
        scientific_names = list()
        for i in taxa:
            taxon = i.split(";")
            # Query occurrences of given taxon
            if (taxon[1] == "scientificName"):
                scientific_names_tmp = [taxon[0]]
            else:
                if (taxon[1] == "order"):
                    taxa_db = Taxa.query.filter_by(order=taxon[0])
                if (taxon[1] == "family"):
                    taxa_db = Taxa.query.filter_by(family=taxon[0])
                if (taxon[1] == "genus"):
                    taxa_db = Taxa.query.filter_by(genus=taxon[0])
                scientific_names_tmp = [
                    i.scientificName for i in taxa_db if i.scientificName]
            scientific_names = scientific_names+list(scientific_names_tmp)
        scientific_names = np.unique(scientific_names)
        # Get occurrences for selected taxa
        #occurrences_db = Occurrences.query.filter(Occurrences.scientificName.in_(scientific_names)).all()
        occurrences_db = Occurrences.query\
            .join(Identification_events, Occurrences.identificationID==Identification_events.identificationID)\
            .with_entities(Occurrences.occurrenceID, Identification_events.scientificName)\
            .filter(Identification_events.scientificName.in_(scientific_names))\
            .all()
        occurrence_ids = tuple(
            np.unique([i.occurrenceID for i in occurrences_db if i.occurrenceID]))
        # Get images for selected taxa
        occurrence_images = Occurrence_images.query\
            .join(Occurrences, Occurrence_images.occurrenceID == Occurrences.occurrenceID)\
            .join(Identification_events, Occurrences.identificationID==Identification_events.identificationID)\
            .with_entities(Occurrence_images.id, Occurrence_images.filename, Occurrence_images.imageCategory, Occurrence_images.comment, Occurrence_images.occurrenceID, Identification_events.scientificName)\
            .filter(Occurrence_images.occurrenceID.in_(occurrence_ids))\
            .filter(Occurrence_images.imageCategory.in_(image_categories))\
            .all()
        taxa1 = [i.scientificName for i in occurrence_images]
        # list of occurrenceIDs associated with images
        #occurrenceIDs_imaged = [
        #    i.occurrenceID for i in occurrence_images if i.occurrenceID]
        # taxa associated with occurrenceIDs
        #imaged_taxa = Taxa.query\
        #    .join(Identification_events, Taxa.scientificName == Identification_events.scientificName)\
        #    .join(Occurrences, Identification_events.identificationID==Occurrences.identificationID)\
        #    .with_entities(Taxa.scientificName, Taxa.taxonRank, Taxa.genus, Taxa.specificEpithet, Taxa.scientificNameAuthorship, Occurrences.occurrenceID)\
        #    .filter(Occurrences.occurrenceID.in_(occurrenceIDs_imaged))\
        #    .all()
        
        # Get illustrations for selected taxa
        illustration_images = Illustrations.query.filter(Illustrations.scientificName.in_(scientific_names)).filter(Illustrations.category.in_(image_categories)).all()
        taxa2 = [i.scientificName for i in illustration_images]
        # Make a list of imaged taxa
        taxa_list = []
        for i in taxa1+taxa2:
            if i not in taxa_list:
                taxa_list.append(i)
        imaged_taxa = Taxa.query.filter(Taxa.scientificName.in_(taxa_list)).all()
        # Render html
        # Button for displaying images
        if request.form.get('action1') == 'VALUE1':
            return render_template("taxon_image.html", title=title, user=current_user, dropdown_names=dropdown_names, dropdown_ranks=dropdown_ranks, imagecat=imagecat, images=occurrence_images, illustration_images=illustration_images, imaged_taxa=imaged_taxa, dir_path=dir_path)
        # Button for creating landmark-dataset
        if request.form.get('action2') == 'VALUE2':
            # Return error message if more than one image-category
            image_ids = [i.id for i in occurrence_images]
            taxa = " | ".join([i.split(";")[0] for i in taxa])
            if len(image_categories) > 1:
                flash(f'Only one image category should be selected!', category="error")
                return redirect(url_for("taxa.taxon_image"))
            image_categories = "".join(image_categories)
            if len(image_ids) < 1:
                flash(f'At least one taxon with one image should be selected', category="error")
                return redirect(url_for("taxa.taxon_image"))
            image_ids = " | ".join(str(i) for i in image_ids)
            # Send parameters to new_landmarks route
            return redirect(url_for('landmarks.landmark_add_dataset', taxa=taxa, image_category=image_categories, image_ids=image_ids))
    else:
        return render_template("taxon_image.html", title=title, user=current_user, dropdown_names=dropdown_names, dropdown_ranks=dropdown_ranks, imagecat=imagecat)


@taxa.route('/det_labels', methods=["POST", "GET"])
@login_required
def det_labels():
    title = "Print determination labels"
    # Remove earlier qr-code image-files
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    for file in files:
        if file.startswith(f'{current_user.id}_detqrlabel_'):
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], file))
    # Post
    if request.method == 'POST':
        # Button 1: Add eventID and number of labels to be printed
        if request.form.get('action1') == 'VALUE1':
            # Get data from form
            scientificName = request.form.get("scientificName")
            identificationQualifier = request.form.get("identificationQualifier")
            sex = request.form.get("sex")
            label_number = request.form.get("Label_number")
            # Add new eventID to temporary databse
            new_det = Print_det(
                scientificName=scientificName, identificationQualifier=identificationQualifier, sex=sex, print_n=label_number, createdByUserID=current_user.id)
            db.session.add(new_det)
            db.session.commit()
        # Button 2: Clear table
        if request.form.get('action2') == 'VALUE2':
            # Delete all records in print_events table
            Print_det.query.filter_by(
                createdByUserID=current_user.id).delete()
            db.session.commit()
        # Button 3: Print lables
        if request.form.get('action3') == 'VALUE3':
            # Finn eventIDer og antall etiketter som skal printes av brukeren
            user = current_user
            dets = user.print_det
            # Dersom ingen event-id er valgt
            if not dets:
                flash("At least one scientific name must be added", category="error")
            else:
                # Query Taxa-table for selected scientific names
                det_data = Taxa.query\
                    .filter(Taxa.scientificName.in_([det.scientificName for det in dets]))\
                    .order_by(Taxa.scientificName.desc())\
                    .all()
                # Create qrcodes
                for det in dets:
                    for data in det_data:
                        if det.scientificName==data.scientificName:
                            for n in range(det.print_n):
                                filename = f'{current_user.id}_detqrlabel_{det.id}_{n}.png'
                                #qr = qrcode.QRCode(version = 1, box_size = 5, border = 1, error_correction=qrcode.constants.ERROR_CORRECT_L)
                                #qr.add_data(f'TAX:{data.taxonInt}:{det.identificationQualifier}:{det.sex}:{new_unit_id()}')
                                #qr.make(fit = True)
                                #img = qr.make_image(fill_color = 'black', back_color = 'white')
                                #img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                                encoded_data = encode(f'TAX:{data.taxonInt}:{det.identificationQualifier}:{det.sex}:{new_unit_id()}'.encode('utf8'))
                                image = Image.frombytes('RGB', (encoded_data.width, encoded_data.height), encoded_data.pixels)
                                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Return labels
                return render_template("taxon_labels_output.html", title=title, dets=dets, user=current_user, det_data=det_data)

    # Søk etter Taxa
    taxa = Taxa.query.all()
    # Return
    return render_template("taxon_labels.html", title=title, taxa=taxa, user=current_user)
