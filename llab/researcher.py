from flask import Blueprint, render_template, flash, request, jsonify
from flask_login import login_required, current_user
from .models import Collectors
from . import db

researcher = Blueprint('researcher', __name__)

@researcher.route('/add_researcher', methods=["POST", "GET"])
@login_required
def add_researcher():
    title = "Add researcher"
    if request.method == 'POST':
        # Get input from form
        recordedBy = request.form.get("fullname")
        recordedByID = request.form.get("researcherid")
        # Query email in database
        recordedBy_test = Collectors.query.filter_by(
            recordedBy=recordedBy).first()
        recordedByID_test = Collectors.query.filter_by(
            recordedByID=recordedByID).first()
        # Check input is correct. If success add researcher to database. If error send error message
        if recordedBy_test:
            flash('Researchers name aready exists', category='error')
        elif len(recordedBy) < 6:
            flash(
                'Researcher name is to short. Should include more than five characters.', category='error')
        elif len(recordedByID) < 1:
            # New Print_events object
            new_collector = Collectors(
                recordedBy=recordedBy, recordedByID=recordedByID, createdByUserID=current_user.id)
            # Add new objects to database
            db.session.add(new_collector)
            # Commit
            db.session.commit()
            flash(
                f'{recordedBy} was added to the list of researchers, but without a researcher ID', category='success')
        elif len(recordedByID) < 6:
            flash(
                'Researcher ID is to short. Should include more than five characters.', category='error')
        elif recordedByID == 'https://orcid.org/0000-0000-0000-0000':
            flash('The researcher ID field has to be edited.', category='error')
        elif recordedByID_test:
            flash('Researchers ID aready exists', category='error')
        else:
            # New Print_events object
            new_collector = Collectors(
                recordedBy=recordedBy, recordedByID=recordedByID, createdByUserID=current_user.id)
            # Add new objects to database
            db.session.add(new_collector)
            # Commit
            db.session.commit()
            flash(f'{recordedBy} was added to the list of researchers',
                  category='success')
    # Return HTML page
    return render_template("researcher_add.html", title=title, user=current_user)
