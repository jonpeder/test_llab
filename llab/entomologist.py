from flask import Blueprint, render_template, flash, request, jsonify
from flask_login import login_required, current_user
from .models import Collectors
from . import db

entomologist = Blueprint('entomologist', __name__)

@entomologist.route('/add_entomologist', methods=["POST", "GET"])
@login_required
def add_entomologist():
    title = "Add entomologist"
    if request.method == 'POST':
        # Get input from form
        recordedBy = request.form.get("fullname")
        recordedByID = request.form.get("researcherid")
        # Query email in database
        recordedBy_test = Collectors.query.filter_by(
            recordedBy=recordedBy).first()
        recordedByID_test = Collectors.query.filter_by(
            recordedByID=recordedByID).first()
        # Check input is correct. If success add entomologist to database. If error send error message
        if recordedBy_test:
            flash('Entomologists name aready exists', category='error')
        elif len(recordedBy) < 6:
            flash(
                'Entomologist name is to short. Should include more than five characters.', category='error')
        elif len(recordedByID) < 1:
            # New Print_events object
            new_collector = Collectors(
                recordedBy=recordedBy, recordedByID=recordedByID, createdByUserID=current_user.id)
            # Add new objects to database
            db.session.add(new_collector)
            # Commit
            db.session.commit()
            flash(
                f'{recordedBy} was added to the list of entomologists, but without a researcher ID', category='success')
        elif len(recordedByID) < 6:
            flash(
                'Entomologist ID is to short. Should include more than five characters.', category='error')
        elif recordedByID == 'https://orcid.org/0000-0000-0000-0000':
            flash('The entomologist ID field has to be edited.', category='error')
        elif recordedByID_test:
            flash('Entomologists ID aready exists', category='error')
        else:
            # New Print_events object
            new_collector = Collectors(
                recordedBy=recordedBy, recordedByID=recordedByID, createdByUserID=current_user.id)
            # Add new objects to database
            db.session.add(new_collector)
            # Commit
            db.session.commit()
            flash(f'{recordedBy} was added to the list of entomologists',
                  category='success')
    # Return HTML page
    return render_template("add_entomologist.html", title=title, user=current_user)
