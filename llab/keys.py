from flask import Blueprint, current_app, redirect, url_for, request, render_template, flash
from flask_login import login_required, current_user
from .models import User, Hierarchical_keys, Hierarchical_key_options, Taxa, Illustrations
from .functions import parse_identification_key
from . import db
import numpy as np
from .filters import italicize_scientific_name

# connect to __init__ file
keys = Blueprint('keys', __name__)
# Specify app
app = current_app

@keys.route('/key_add', methods=["POST", "GET"])
@login_required
def key_add():
    title = "Add new identification key"
    # Get list of taxa from database
    taxa = Taxa.query.all()
    # Post
    if request.method == 'POST':
        # Get input data
        name = request.form.get("name")
        description = request.form.get("description")
        taxonID = request.form.get("taxonID")
        bibliographicReference = request.form.get("bibliographicReference")
        # Control that name is not already used and that a taxon is selected
        already_existing_name = Hierarchical_keys.query.filter_by(name=name).first()
        if already_existing_name:
            flash('This name does aready exist', category='error')
        elif not taxonID:
            flash('Select a taxon from the dropdown list', category='error')
        else:
        # Add to database
            new_key = Hierarchical_keys(name=name, description=description, taxonID=taxonID, bibliographicReference=bibliographicReference, userID=current_user.id)
            # Add new objects to database
            db.session.add(new_key)
            # Commit
            db.session.commit()
            flash(f'{name} is added as a new identification key!', category="success")
            # If an identification key have been entered, add the content to the database.
            if request.form.get("input_key"):
                input_key_list = parse_identification_key(request.form.get("input_key")) # Parse the key through the parse_identification_key function which outputs a list of each parent-child relation in the key, including character descriptions and comments.
                for child in input_key_list:
                    # Check if parent of the child exist in database
                    dichKey = Hierarchical_keys.query.filter_by(name=name).first() # Get keyID
                    existing_parent = Hierarchical_key_options.query.filter_by(keyID=dichKey.id, name=child["parent"]).first()
                    if existing_parent:
                        parent = existing_parent.id
                    else:
                        parent = 0                    
                    # Add to database
                    new_child = Hierarchical_key_options(parent=parent, keyID=dichKey.id, name=child["child"], question=child["text_content"], comment=child["comment"])
                    # Add new objects to database
                    db.session.add(new_child)
                    # Commit
                    db.session.commit()

    # Return html-page
    return render_template("key_add.html", title=title, user=current_user, taxa=taxa)

@keys.route('/key_view', methods=["POST", "GET"])
@login_required
def key_view():
    title = "Identification key"
    possible_names = []
    current_step = []
    key_id = None
    reached_conclusion = False
    conclusion_name = None
    conclusion_figures = None
    suggested_identificationKeys = None

    # Get list of identification keys
    keys = Hierarchical_keys.query.all()
    # Get list of taxa from database
    taxa = Taxa.query.all()
    
    # Post
    # Button 2: Edit key
    if request.method == 'POST' and request.form.get('action2') == 'VALUE2':
        title = "Edit Identification Key"
        key_id = request.args.get('identification_key') or request.form.get('identification_key')
        key = None
        options = []
        illustrations = Illustrations.query.join(Taxa, Illustrations.taxonID == Taxa.taxonInt, isouter=False)\
                    .with_entities(Illustrations.id, Illustrations.filename, Illustrations.imageType, \
                    Illustrations.category, Illustrations.sex, Illustrations.scaleBar, Taxa.scientificName, \
                    Taxa.taxonRank, Taxa.order, Taxa.family, Taxa.genus).all()
    
            
        # Prepare list of taxa for dropdown-select-search bar
        order = tuple(np.unique([i.order for i in taxa if i.order]))
        family = tuple(np.unique([i.family for i in taxa if i.family]))
        genus = tuple(np.unique([i.genus for i in taxa if i.genus]))
        scientificName = tuple(np.unique([i.scientificName for i in taxa]))
        dropdown_names = order+family+genus+scientificName
        dropdown_ranks = tuple(len(order)*["order"]+len(family)*["family"]+len(genus)*[
                           "genus"]+len(scientificName)*["scientificName"])
    
        # Get unique values for filter dropdowns
        categories = db.session.query(Illustrations.category).distinct().all()
        sexes = db.session.query(Illustrations.sex).distinct().all()
    
        if key_id:
            key = Hierarchical_keys.query.filter_by(id=key_id).first()
            options = Hierarchical_key_options.query.filter_by(keyID=key_id).order_by(Hierarchical_key_options.parent, Hierarchical_key_options.id).all()
    
        return render_template("key_edit.html", 
                         title=title, 
                         user=current_user, 
                         key=key, 
                         options=options,
                         illustrations=illustrations,
                         categories=[c[0] for c in categories if c[0]],
                         sexes=[s[0] for s in sexes if s[0]],
                         dropdown_names=dropdown_names,
                         dropdown_ranks=dropdown_ranks,
                         taxa=taxa,
                         get_figures_for_display=get_figures_for_display)

    # Button 1: Display key
    if request.method == 'POST' and request.form.get('action1') == 'VALUE1':
        key_id = request.form.get("identification_key")   
        if key_id:
            # Get first step (options with parent 0)
            current_step = Hierarchical_key_options.query.filter_by(
                keyID=key_id, parent=0
            ).all()
            
            # Get all possible names for this key
            all_options = Hierarchical_key_options.query.filter_by(keyID=key_id).all()
            possible_names = get_possible_names(all_options, current_step)
            
    # If step_id is provided via GET (for navigation)
    step_id = request.args.get('step_id')
    if step_id:
        key_id = request.args.get('key_id')
        if key_id:
            # Get next step (children of selected option)
            current_step = Hierarchical_key_options.query.filter_by(
                keyID=key_id, parent=step_id
            ).all()
            
            # Get the selected option to check if it's terminal
            selected_option = Hierarchical_key_options.query.filter_by(id=step_id).first()
            
            # Get all options for this key
            all_options = Hierarchical_key_options.query.filter_by(keyID=key_id).all()
            possible_names = get_possible_names(all_options, current_step)
            
            # Check if we reached a conclusion (terminal option with only one possible name)
            if not current_step and selected_option:
                reached_conclusion = True
                # Get the conclusion name
                if selected_option.taxonID:
                    taxon = Taxa.query.filter_by(taxonInt=selected_option.taxonID).first()
                    suggested_identificationKeys = Hierarchical_keys.query.filter_by(taxonID=selected_option.taxonID).all()
                    conclusion_name = taxon.scientificName if taxon else selected_option.name
                    conclusion_figures = Illustrations.query.filter_by(taxonID=selected_option.taxonID).all()
                    conclusion_figures = " | ".join([f':{i.id}' for i in conclusion_figures])
                else:
                    conclusion_name = selected_option.name
                    conclusion_figures = selected_option.figures

    
    return render_template("key_view.html", 
                         title=title, 
                         user=current_user, 
                         current_step=current_step,
                         possible_names=possible_names,
                         key_id=key_id,
                         keys=keys,
                         reached_conclusion=reached_conclusion,
                         conclusion_name=conclusion_name,
                         conclusion_figures=conclusion_figures,
                         taxa=taxa,
                         suggested_identificationKeys=suggested_identificationKeys,
                         get_figures_for_display=get_figures_for_display)

def get_possible_names(all_options, current_step):
    """Get all possible names reachable from current step"""
    possible_names = set()
    
    def find_reachable_names(option_id):
        """Recursively find all terminal names reachable from an option"""
        children = [opt for opt in all_options if opt.parent == option_id]
        
        if not children:
            # This is a terminal option, add its name if it's not numeric
            option = next((opt for opt in all_options if opt.id == option_id), None)
            if option and not option.name.replace('.', '').isdigit():
                # Use taxonID if available, otherwise use name
                if option.taxonID:
                    taxon = Taxa.query.filter_by(taxonInt=option.taxonID).first()
                    if taxon:
                        possible_names.add(taxon.scientificName)
                    else:
                        possible_names.add(option.name)
                else:
                    possible_names.add(option.name)
        else:
            # Continue recursively with children
            for child in children:
                find_reachable_names(child.id)
    
    # Start from each option in current step
    for option in current_step:
        find_reachable_names(option.id)
    
    return sorted(list(possible_names))

@keys.route('/key_edit', methods=["POST", "GET"])
@login_required
def key_edit():
    title = "Edit Identification Key"
    key_id = request.args.get('key_id') or request.form.get('key_id')
    key = None
    options = []
    illustrations = Illustrations.query.join(Taxa, Illustrations.taxonID == Taxa.taxonInt, isouter=False)\
                    .with_entities(Illustrations.id, Illustrations.filename, Illustrations.imageType, \
                    Illustrations.category, Illustrations.sex, Illustrations.scaleBar, Taxa.scientificName, \
                    Taxa.taxonRank, Taxa.order, Taxa.family, Taxa.genus).all()
    
            
    # Prepare list of taxa for dropdown-select-search bar
    taxa = Taxa.query.all()  # Database query for taxa
    order = tuple(np.unique([i.order for i in taxa if i.order]))
    family = tuple(np.unique([i.family for i in taxa if i.family]))
    genus = tuple(np.unique([i.genus for i in taxa if i.genus]))
    scientificName = tuple(np.unique([i.scientificName for i in taxa]))
    dropdown_names = order+family+genus+scientificName
    dropdown_ranks = tuple(len(order)*["order"]+len(family)*["family"]+len(genus)*[
                           "genus"]+len(scientificName)*["scientificName"])
    
    # Get unique values for filter dropdowns
    categories = db.session.query(Illustrations.category).distinct().all()
    sexes = db.session.query(Illustrations.sex).distinct().all()
    
    if key_id:
        key = Hierarchical_keys.query.filter_by(id=key_id).first()
        options = Hierarchical_key_options.query.filter_by(keyID=key_id).order_by(Hierarchical_key_options.parent, Hierarchical_key_options.id).all()
    
    # POST
    if request.method == 'POST':
        if request.form.get("DELETE") == "delete":
            key_id = request.form.get('key_id')
            title = request.form.get('title')
            # Delete related options
            delete_options = Hierarchical_key_options.query.filter_by(keyID=key_id).all()
            for option in delete_options:
                db.session.delete(option)
            # Delete the main key
            delete_key = Hierarchical_keys.query.filter_by(id=key_id).first()
            if delete_key:
                db.session.delete(delete_key)
            # Commit changes
            db.session.commit()
            flash(f'{title} deleted!', category="success")
            return redirect(url_for('keys.key_view'))

        elif request.form.get("UPDATE") == "update":
            key_id = request.form.get('key_id')
            title = request.form.get('title')
            description = request.form.get('description')
            bibliographicReference = request.form.get('bibliographicReference')
            # Update Hierarchical_keys table
            key = Hierarchical_keys.query.filter_by(id=key_id).first()
            key.name = title
            key.description = description
            key.bibliographicReference = bibliographicReference
            # Commit
            db.session.commit()
            flash(f'{title} updated!', category="success")
        else:
            # If key ID exist
            key_id = request.args.get('key_id') or request.form.get('key_id')
            if key_id:
                # Get data from input form. Each option has a separate form and only one form can be submitted at a time.
                update_option_id = request.form.get('option_id')
                parent = request.form.get('parent')
                option_name = request.form.get('option_name')
                taxonID = request.form.get('taxonID')
                if taxonID == "":
                    taxonID = None
                question = request.form.get('question')
                comment = request.form.get('comment')
                selected_figures = request.form.get('selected_figures')
                # Update database
                option = Hierarchical_key_options.query.filter_by(id=update_option_id).first()
                option.taxonID = taxonID
                option.parent = parent
                option.name = option_name
                option.question = question
                option.comment = comment
                option.figures = selected_figures
                # Commit
                db.session.commit()
                flash(f'Option {update_option_id} updated!', category="success")


    return render_template("key_edit.html", 
                         title=title, 
                         user=current_user, 
                         key=key, 
                         options=options,
                         illustrations=illustrations,
                         categories=[c[0] for c in categories if c[0]],
                         sexes=[s[0] for s in sexes if s[0]],
                         dropdown_names=dropdown_names,
                         dropdown_ranks=dropdown_ranks,
                         taxa=taxa,
                         get_figures_for_display=get_figures_for_display)
                         


@keys.route('/test_figure_modal', methods=["POST", "GET"])
@login_required
def test_figure_modal():
    title = "Test figure modal"
    illustrations = Illustrations.query.join(Taxa, Illustrations.taxonID == Taxa.taxonInt, isouter=False)\
                    .with_entities(Illustrations.id, Illustrations.filename, Illustrations.imageType, \
                    Illustrations.category, Illustrations.sex, Illustrations.scaleBar, Taxa.scientificName, \
                    Taxa.taxonRank, Taxa.order, Taxa.family, Taxa.genus).all()
    
            
    # Prepare list of taxa for dropdown-select-search bar
    taxa = Taxa.query.all()  # Database query for taxa
    order = tuple(np.unique([i.order for i in taxa if i.order]))
    family = tuple(np.unique([i.family for i in taxa if i.family]))
    genus = tuple(np.unique([i.genus for i in taxa if i.genus]))
    scientificName = tuple(np.unique([i.scientificName for i in taxa]))
    dropdown_names = order+family+genus+scientificName
    dropdown_ranks = tuple(len(order)*["order"]+len(family)*["family"]+len(genus)*[
                           "genus"]+len(scientificName)*["scientificName"])
    
    # Get unique values for filter dropdowns
    categories = db.session.query(Illustrations.category).distinct().all()
    sexes = db.session.query(Illustrations.sex).distinct().all()
    
    return render_template("test_figure_modal.html", 
                         title=title, 
                         user=current_user, 
                         illustrations=illustrations,
                         categories=[c[0] for c in categories if c[0]],
                         sexes=[s[0] for s in sexes if s[0]],
                         dropdown_names=dropdown_names,
                         dropdown_ranks=dropdown_ranks)

def get_figures_for_display(figures_format):
    figures_list = figures_format.split(" | ")
    figures_dict_list = []
    for figure in figures_list:
        figure_number = figure.split(":")[0]
        illustration_id = figure.split(":")[1]
        figure_data = Illustrations.query\
                .join(Taxa, Illustrations.taxonID == Taxa.taxonInt, isouter=False)\
                .filter(Illustrations.id == illustration_id)\
                .with_entities(
                    Illustrations.id, 
                    Illustrations.filename, 
                    Taxa.scientificName, 
                    Illustrations.category,
                    Illustrations.perspective, 
                    Illustrations.sex, 
                    Illustrations.rightsHolder, 
                    Illustrations.associatedReference, 
                    Illustrations.remarks, 
                    Illustrations.imageType,
                    Illustrations.scaleBar
                ).first()
        
        filename = figure_data.filename
        taxon_name = figure_data.scientificName
        category = figure_data.category
        perspective = figure_data.perspective
        sex = figure_data.sex
        scalebar = figure_data.scaleBar
        rightsholder = figure_data.rightsHolder
        reference = figure_data.associatedReference
        remarks = figure_data.remarks
        imagetype = figure_data.imageType
        
        # Create figure text
        figure_text = italicize_scientific_name(taxon_name)
        if sex:
            figure_text = figure_text + " " + sex
        if category:
            figure_text = figure_text + ", " + category
        if perspective:
            figure_text = figure_text + ", " + perspective + " view"
        figure_text = figure_text + ". "
        if scalebar:
            figure_text = figure_text + f"Scalebar {scalebar}. "
        if remarks:
            figure_text = figure_text + remarks.capitalize() + ". "
        if imagetype:
            figure_text = figure_text + imagetype.capitalize()
        if rightsholder:
            figure_text = figure_text + ", " + rightsholder.capitalize()
        if reference:
            figure_text = figure_text + f" ({reference})"
        
        # Add data to a new dictionary
        figure_dict = {
            "figure_number": figure_number,
            "filename": filename,
            "figure_text": figure_text
        }
        # Append dictionary to list
        figures_dict_list.append(figure_dict)
    return(figures_dict_list)
