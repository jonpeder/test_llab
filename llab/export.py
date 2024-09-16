# Flask module for handling datasets
from flask import Blueprint, current_app, redirect, url_for, render_template, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from .models import User, Collecting_events, Occurrences, Country_codes, Eunis_habitats
from . import db
import numpy as np
import pandas as pd
import csv
from .filters import format_dates, leg_format, locality_format

# connect to __init__ file
export = Blueprint('export', __name__)

# Specify app
app = current_app

def remove_bold (txt):
    txt = txt.replace("<b>","")
    txt = txt.replace("</b>", "")
    return(txt)

# Add specimens to dataset
@export.route('/export_events', methods=['POST'])
def export_events():
    if request.json: # Check if data is received
        data = request.json # Get the data
        if data['ids'] == []: # Check if records are selected
            return jsonify({"status": "error", "message": "No events in query"})
        else:
            event_ids = np.unique(data['ids']) # Get the event-IDs
            events = Collecting_events.query.filter(Collecting_events.eventID.in_(event_ids)).all() # Get the dataset
            # Format a list for export
            header = ["CollectingEventID", "CountryCode", "State/Province", "County", "Municipality", "Locality", "Habitat", "DecimalDeg", "googleMapsLink", "Radius", "SamplingProtocol", "date", "recordedBy", "Remarks", "databased"]
            export_list = []
            for event in events:
                row = [event.eventID, event.countryCode, event.stateProvince, event.county, event.municipality, locality_format(event.locality_1, event.locality_2), event.habitat, f'{event.decimalLatitude}, {event.decimalLongitude}', f"http://maps.google.com/maps?q={event.decimalLatitude},{event.decimalLongitude}", event.coordinateUncertaintyInMeters, event.samplingProtocol, remove_bold(format_dates(event.eventDate_1, event.eventDate_2)), leg_format(event.recordedBy), event.eventRemarks, event.databased]
                export_list.append(row)
            with open('/var/www/llab/llab/static/events.csv', 'w', encoding='utf-8') as f:
                # using csv.writer method from CSV package
                write = csv.writer(f)
                write.writerow(header)
                write.writerows(export_list)
            return send_file(
                    '/var/www/llab/llab/static/events.csv',
                    mimetype='text/csv',
                    download_name='events.csv',
                    as_attachment=True
                )
    else:
        return jsonify({"status": "error", "message": "No data received"})