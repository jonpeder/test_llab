from flask import Blueprint, current_app, flash, request, redirect, url_for, render_template, send_from_directory
from flask_login import login_required, current_user
from .models import User, Collecting_events, Event_images
from . import db
import os

# connect to __init__ file
queries = Blueprint('queries', __name__)

@queries.route('/show_event', methods=['GET', 'POST'])
@login_required
def show_event():
    title = "Show collecting events"
    events = Collecting_events.query.filter_by(createdByUserID = current_user.id).order_by(Collecting_events.eventID.desc())
    if request.method == 'POST':
        eventID = request.form.get("eventID")
        # Button 1:
        if request.form.get('action1') == 'VALUE1':
            event = Collecting_events.query.filter_by(eventID = eventID)
            files = Event_images.query.filter_by(eventID=eventID)
            return render_template("show_event.html", title = title, user=current_user, files=files, events=events, event=event)
    else:
        return render_template("show_event.html", title = title, user=current_user, events=events)
