# Flask mudule for managing information about the insect collection
from .functions import newDrawerName
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Occurrences, Drawers, Units
from . import db

collection = Blueprint('collection', __name__)

@collection.route('/drawer_edit', methods=["POST", "GET"])
@login_required
def drawer_edit():
    if request.method == 'POST':
        if request.form.get("add_drawer") == "add_drawer":
            existing_drawer_names = [i.drawerName for i in Drawers.query.all()] # Get all drawer names
            # Get input from form
            new_drawer_name = request.form.get("drawer-new-name")
            # Add integer to drawer name to make it unique
            new_drawer_name = newDrawerName(existing_drawer_names, new_drawer_name)
            # Check input is correct. If success add drawer to database. If error send error message
            if new_drawer_name in existing_drawer_names:
                flash(f'Drawer name {new_drawer_name} already exists', category='error')
            elif len(new_drawer_name) < 3:
                flash('Drawer name is to short. Should include more than two characters.', category='error')
            elif len(new_drawer_name) > 25:
                flash('Drawer name is to long. Should include less than 25 characters.', category='error')
            else:
                # New Drawers object
                new_drawer = Drawers(drawerName=new_drawer_name, createdByUserID=current_user.id)
                # Add new objects to database
                db.session.add(new_drawer)
                # Commit
                db.session.commit()
                flash(f'{new_drawer_name} was added to the list of drawers', category='success')
        if request.form.get("update_drawer") == "update_drawer":
            # Get input from form
            drawer_name = request.form.get("drawer-name")
            unit_ids = request.form.get("unit_ids")
            if unit_ids == "":
                flash('No units were selected', category='error')
            else:
                # Get units and specimens
                unit_ids = unit_ids.splitlines()
                specimens = Occurrences.query.filter(Occurrences.unit_id.in_(unit_ids)).all()
                units = Units.query.filter(Units.unitID.in_(unit_ids)).all()
                # If no units were found
                if len(units) == 0:
                    flash('No units were found', category='error')
                else:
                    # If no specimens were found
                    if len(specimens) == 0:
                        flash('No specimens were found in the selected units', category='error')
                    # Update drawer name for all specimens
                    for unit in units:
                        unit.drawerName = drawer_name
                    # Commit
                    db.session.commit()
                    flash(f'{drawer_name} was updated for {len(units)} units with {len(specimens)} specimens', category='success')
        if request.form.get("delete_drawer") == "delete_drawer":
            # Get input from form
            drawer_name = request.form.get("drawer-name")
            # Get all specimens in the drawer
            units = Units.query.filter(Units.drawerName == drawer_name).all()
            specimens = Occurrences.query.join(Units, Units.unitID == Occurrences.unit_id).filter(Units.drawerName == drawer_name).all()
            # Update drawer name for all specimens
            for unit in units:
                unit.drawerName = None
            # Commit
            db.session.commit()
            # Delete drawer
            drawer = Drawers.query.filter(Drawers.drawerName == drawer_name).first()
            db.session.delete(drawer)
            # Commit
            db.session.commit()
            flash(f'{drawer_name} deleted and {len(specimens)} specimens in {len(units)} units removed from the drawer', category='success')
    existing_drawer_names = [i.drawerName for i in Drawers.query.all()] # Get all drawer names
    # Return HTML page
    return render_template("drawer_add.html", user=current_user, existing_drawer_names=existing_drawer_names)