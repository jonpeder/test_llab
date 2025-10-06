# load packages
from .functions import bar_plot_dict
from flask import Blueprint, request, render_template, flash, request
from flask_login import login_required, current_user
from sqlalchemy import and_, or_
from .models import Occurrences, Taxa, Identification_events, Collecting_events, Country_codes, Eunis_habitats, Datasets, Units, Drawers, co1, Observations
from . import db
import numpy as np
import pandas as pd
import json

# connect to __init__ file
filter = Blueprint('filter', __name__)

def build_filter_query():
    """Build a filtered query based on form parameters"""
    query = Occurrences.query\
        .join(Identification_events, Occurrences.identificationID == Identification_events.identificationID, isouter=True)\
        .join(Taxa, Identification_events.scientificName == Taxa.scientificName, isouter=True)\
        .join(Collecting_events, Occurrences.eventID == Collecting_events.eventID, isouter=True)\
        .join(Country_codes, Collecting_events.countryCode == Country_codes.countryCode, isouter=True)\
        .join(Eunis_habitats, Collecting_events.eunisCode == Eunis_habitats.eunisCode, isouter=True)\
        .join(co1, Occurrences.occurrenceID == co1.occurrenceID, isouter=True)

    # Polygon spatial filter (added this section)
    if request.form.get("polygon_event_ids"):
        polygon_event_ids = request.form.get("polygon_event_ids").split(',')
        polygon_event_ids = [event_id.strip() for event_id in polygon_event_ids if event_id.strip()]
        if polygon_event_ids:
            query = query.filter(Collecting_events.eventID.in_(polygon_event_ids))
            
    # QR Code filters (OR relationship between different QR types)
    qr_filters = []
    
    if request.form.get("occurrence_ids"):
        specimen_qr = request.form.get("occurrence_ids").splitlines()
        specimen_qr = [i.replace("http://purl.org/nhmuio/id/", "") for i in specimen_qr]
        qr_filters.append(Occurrences.occurrenceID.in_(specimen_qr))
    
    if request.form.get("unit_ids"):
        unit_qr = request.form.get("unit_ids").splitlines()
        qr_filters.append(Occurrences.unit_id.in_(unit_qr))
    
    if request.form.get("drawer_name"):
        drawer_qr = request.form.get("drawer_name").splitlines()
        qr_filters.append(Units.drawerName.in_(drawer_qr))
    
    if qr_filters:
        query = query.filter(or_(*qr_filters))

    # Taxon filter
    if request.form.get("taxon_name"):
        taxon_filters = []
        taxon = request.form.get("taxon_name")
        taxon_name = taxon.split(" [")[0]
        taxon_rank = taxon.split(" [")[1][:-1]
        if taxon_rank == "scientificName":
            taxon_filters.append(Identification_events.scientificName == taxon_name)
        else:
            rank_filters = []
            if taxon_rank == "class":
                rank_filters.append(Taxa.cl == taxon_name)
            elif taxon_rank == "order":
                rank_filters.append(Taxa.order == taxon_name)
            elif taxon_rank == "family":
                rank_filters.append(Taxa.family == taxon_name)
            elif taxon_rank == "genus":
                rank_filters.append(Taxa.genus == taxon_name)
            
            # Get scientific names for this taxon group
            scientific_names = db.session.query(Taxa.scientificName)\
                .filter(or_(*rank_filters))\
                .subquery()
            taxon_filters.append(Identification_events.scientificName.in_(scientific_names))

        if taxon_filters:
            query = query.filter(or_(*taxon_filters))

    # Simple filters
    filter_mappings = [
        ("taxon_rank", Taxa.taxonRank),
        ("sex", Identification_events.sex),
        ("eventID", Collecting_events.eventID),
        ("method", Collecting_events.samplingProtocol),
    ]
    
    for form_field, model_field in filter_mappings:
        if request.form.get(form_field):
            query = query.filter(model_field == request.form.get(form_field))

    # Locality filters
    locality_filters = []
    if request.form.get("municipality"):
        locality_filters.append(Collecting_events.municipality == request.form.get("municipality"))
    elif request.form.get("county"):
        locality_filters.append(Collecting_events.county == request.form.get("county"))
    elif request.form.get("country"):
        locality_filters.append(Country_codes.country == request.form.get("country"))
    
    if locality_filters:
        query = query.filter(*locality_filters)

    # Habitat filter
    if request.form.get("eunis"):
        habitat = request.form.get("eunis")
        habitat_filters = [
            Eunis_habitats.level1 == habitat,
            Eunis_habitats.level2 == habitat,
            Eunis_habitats.eunisCode == habitat
        ]
        query = query.filter(or_(*habitat_filters))

    # Date range filter
    if request.form.get("date_from") and request.form.get("date_to"):
        query = query.filter(
            Collecting_events.eventDate_1.between(
                request.form.get("date_from"), 
                request.form.get("date_to")
            )
        )

    # Dataset filter
    if request.form.get("datasetfilter"):
        dataset = Datasets.query.filter_by(datasetName=request.form.get("datasetfilter")).first()
        if dataset and dataset.specimenIDs:
            dataset_ids = dataset.specimenIDs.split(" | ")
            query = query.filter(Occurrences.occurrenceID.in_(dataset_ids))

    return query

def get_dropdown_data():
    """Get all data needed for dropdown menus"""
    collecting_events = Collecting_events.query.all()
    taxa = Taxa.query.all()
    habitats = Eunis_habitats.query.all()  # Make sure this is here
    
    # Unique values for dropdowns
    dropdown_data = {
        'habitats': habitats,  # Add this line
        #'event_ids': np.unique([i.eventID for i in collecting_events if i.eventID]),
        'methods': np.unique([i.samplingProtocol for i in collecting_events if i.samplingProtocol]),
        'datasets': Datasets.query.all(),
        'drawers': [i.drawerName for i in Drawers.query.all()],
        'ranks': np.unique([i.taxonRank for i in taxa if i.taxonRank]),
        'country_codes': np.unique([i.countryCode for i in collecting_events if i.countryCode]),
        'counties': np.unique([i.county for i in collecting_events if i.county]),
        'municipalities': np.unique([i.municipality for i in collecting_events if i.municipality]),
        'habitat_level2': np.unique([h.level2 for h in habitats if h.level2]),
    }
    
    # Countries with names
    countries = []
    for code in dropdown_data['country_codes']:
        country = Country_codes.query.filter_by(countryCode=code).first()
        if country:
            countries.append(country.country)
    dropdown_data['countries'] = countries
    
    # Taxon dropdown
    cl = tuple(np.unique([i.cl for i in taxa if i.cl]))
    order = tuple(np.unique([i.order for i in taxa if i.order]))
    family = tuple(np.unique([i.family for i in taxa if i.family]))
    genus = tuple(np.unique([i.genus for i in taxa if i.genus]))
    scientificName = tuple(np.unique([i.scientificName for i in taxa]))
    
    dropdown_data['dropdown_names'] = cl + order + family + genus + scientificName
    dropdown_data['dropdown_ranks'] = (
        len(cl) * ["class"] + 
        len(order) * ["order"] + 
        len(family) * ["family"] + 
        len(genus) * ["genus"] + 
        len(scientificName) * ["scientificName"]
    )
    
    return dropdown_data


@filter.route('/', methods=["POST", "GET"])
@login_required 
def specimen_filter():
    dropdown_data = get_dropdown_data()
    occurrences = []
    events = []
    metrics_data = {}
    # Initialize filter variables from request
    filters = {
            'taxon_name': '',
            'taxon_rank': '',
            'sex': '',
            'eventID': '',
            'municipality': '',
            'county': '',
            'country': '',
            'method': '',
            'occurrence_ids': '',
            'unit_ids': '',
            'drawer': '',
            'datasetName': '',
            'date_from': request.form.get('date_from'),
            'date_to': request.form.get('date_to')
        }
    if request.method == 'POST' and request.form.get('specimen_filter') == 'specimen_filter':
        filters = {
            'taxon_name': request.form.get('taxon_name'),
            'taxon_rank': request.form.get('taxon_rank'),
            'sex': request.form.get('sex'),
            'eventID': request.form.get('eventID'),
            'municipality': request.form.get('municipality'),
            'county': request.form.get('county'),
            'country': request.form.get('country'),
            'method': request.form.get('method'),
            'occurrence_ids': request.form.get('occurrence_ids'),
            'unit_ids': request.form.get('unit_ids'),
            'drawer': request.form.get('drawer'),
            'datasetName': request.form.get('datasetfilter'),
            'date_from': request.form.get('date_from'),
            'date_to': request.form.get('date_to')
        }
        # Build and execute filtered query
        query = build_filter_query()
        
        occurrences = query.with_entities(
            Occurrences.occurrenceID, Occurrences.preparations, Occurrences.individualCount, 
            Country_codes.country, Collecting_events.eventID, Collecting_events.municipality,
            Collecting_events.locality_1, Collecting_events.locality_2, Collecting_events.habitat,
            Collecting_events.substrateName, Collecting_events.substratePlantPart, Collecting_events.substrateType,
            Collecting_events.eventDate_1, Collecting_events.eventDate_2, Collecting_events.samplingProtocol,
            Collecting_events.recordedBy, Taxa.scientificName, Taxa.genus, Taxa.family, Taxa.order,
            Taxa.taxonRank, Taxa.scientificNameAuthorship, Identification_events.identifiedBy,
            Identification_events.dateIdentified, Identification_events.identificationQualifier,
            Identification_events.sex, Eunis_habitats.level1, Eunis_habitats.level2,
            Eunis_habitats.habitatName, Eunis_habitats.eunisCode, co1.sequenceID
        ).order_by(Taxa.scientificName, Collecting_events.eventID).all()
        
        # Get unique event IDs for events query
        event_ids = list(set(occ.eventID for occ in occurrences if occ.eventID))
        
        if event_ids:
            events = Collecting_events.query.filter(Collecting_events.eventID.in_(event_ids))\
                .join(Eunis_habitats, Collecting_events.eunisCode == Eunis_habitats.eunisCode, isouter=True)\
                .with_entities(
                    Collecting_events.eventID, Collecting_events.decimalLatitude, 
                    Collecting_events.decimalLongitude, Collecting_events.samplingProtocol,
                    Collecting_events.eventDate_1, Eunis_habitats.level1, Eunis_habitats.level2
                ).all()
        
        # Calculate metrics - pass methods from dropdown_data
        metrics_data = calculate_metrics(occurrences, events, dropdown_data['methods'])
        
        # Flash messages for missing occurrences
        if request.form.get("occurrence_ids"):
            specimen_qr = request.form.get("occurrence_ids").splitlines()
            specimen_qr = [i.replace("http://purl.org/nhmuio/id/", "") for i in specimen_qr]
            found_ids = [occ.occurrenceID for occ in occurrences]
            for occ_id in specimen_qr:
                if occ_id not in found_ids:
                    flash(f'{occ_id} not in database', category="error")
    else:
        # For GET requests or when no filter is applied, provide empty metrics
        empty_metric = {'count': [], 'label': []}
        metrics_data = {
            'occ_len': 0,
            'event_len': 0,
            'taxa_len': 0,
            'event_year': empty_metric,
            'event_month': empty_metric,
            'event_method': empty_metric,
            'event_habitat1': empty_metric,
            'event_habitat2': empty_metric,
            'occurrence_year': empty_metric,
            'occurrence_month': empty_metric,
            'occurrence_method': empty_metric,
            'occurrence_habitat1': empty_metric,
            'occurrence_habitat2': empty_metric,
            'occurrence_order': empty_metric,
            'occurrence_family': empty_metric,
            'occurrence_genus': empty_metric,
            'occurrence_taxonRank': empty_metric,
            'met_taxon_count': empty_metric,
            'taxa_year': empty_metric,
            'taxa_taxonRank': empty_metric,
            'taxa_order': empty_metric,
            'taxa_family': empty_metric,
        }
        event_ids = []  # Initialize empty event_ids for GET requests
    
    template_vars = {
        'user': current_user,
        'occurrences': occurrences,
        'events': events,
        'event_ids': event_ids,
        **dropdown_data,
        **metrics_data
    }

    print(filters)

    # Return template
    return render_template("specimen_filter.html", filters=filters, **template_vars)

# Calculate metrics for display
def calculate_metrics(occurrences, events, methods):
    # Handle empty data
    if not occurrences or not events:
        empty_metric = {'count': [], 'label': []}
        return {
            'occ_len': 0,
            'event_len': 0,
            'taxa_len': 0,
            'event_year': empty_metric,
            'event_month': empty_metric,
            'event_method': empty_metric,
            'event_habitat1': empty_metric,
            'event_habitat2': empty_metric,
            'occurrence_year': empty_metric,
            'occurrence_month': empty_metric,
            'occurrence_method': empty_metric,
            'occurrence_habitat1': empty_metric,
            'occurrence_habitat2': empty_metric,
            'occurrence_order': empty_metric,
            'occurrence_family': empty_metric,
            'occurrence_genus': empty_metric,
            'occurrence_taxonRank': empty_metric,
            'met_taxon_count': empty_metric,
            'taxa_year': empty_metric,
            'taxa_taxonRank': empty_metric,
            'taxa_order': empty_metric,
            'taxa_family': empty_metric,
        }
    
    # Query habitats inside the function
    habitats = Eunis_habitats.query.all()
    
    # Create Eunis habitats dictionary
    eunis_dict = {}
    for i in habitats:
        eunis_dict[i.eunisCode] = i.habitatName
    
    # Events metrics
    eventID = []
    samplingProtocol = []
    eventDate_1 = []
    habitat1 = []
    habitat2 = []
    for row in events:
        eventID.append(row.eventID)
        samplingProtocol.append(row.samplingProtocol)
        eventDate_1.append(row.eventDate_1)
        if row.level1:
            habitat1.append(eunis_dict[row.level1])
        else:
            habitat1.append("")
        if row.level2:
            habitat2.append(eunis_dict[row.level2])
        else:
            habitat2.append("")
    
    events_dict = {"EventID":eventID, "samplingProtocol":samplingProtocol, "date":eventDate_1, "habitat1":habitat1, "habitat2":habitat2}
    events_df = pd.DataFrame(events_dict)
    
    # Events metrics - convert numpy arrays to lists
    event_year = bar_plot_dict(events_df, "year", 0)
    event_month = bar_plot_dict(events_df, "month", 0)
    event_method = bar_plot_dict(events_df, "samplingProtocol", 0)
    event_habitat1 = bar_plot_dict(events_df, "habitat1", 0)
    event_habitat2 = bar_plot_dict(events_df, "habitat2", 1)
    
    # Occurrences metrics
    family = []
    order = []
    genus = []
    taxonRank = []
    occ_samplingProtocol = []
    occ_eventDate_1 = []
    occ_habitat1 = []
    occ_habitat2 = []
    for row in occurrences:
        family.append(row.family)
        order.append(row.order)
        genus.append(row.genus)
        taxonRank.append(row.taxonRank)
        occ_samplingProtocol.append(row.samplingProtocol)
        occ_eventDate_1.append(row.eventDate_1)
        if row.level1:
            occ_habitat1.append(eunis_dict[row.level1])
        else:
            occ_habitat1.append("")
        if row.level2:
            occ_habitat2.append(eunis_dict[row.level2])
        else:
            occ_habitat2.append("")
    
    occurrences_dict = {
        "family": family, "order": order, "genus": genus, "taxonRank": taxonRank,
        "samplingProtocol": occ_samplingProtocol, "date": occ_eventDate_1, 
        "habitat1": occ_habitat1, "habitat2": occ_habitat2
    }
    occurrences_df = pd.DataFrame(occurrences_dict)
    
    # Occurrences metrics - convert numpy arrays to lists
    occurrence_year = bar_plot_dict(occurrences_df, "year", 0)
    occurrence_month = bar_plot_dict(occurrences_df, "month", 0)
    occurrence_method = bar_plot_dict(occurrences_df, "samplingProtocol", 0)
    occurrence_order = bar_plot_dict(occurrences_df, "order", 1)
    occurrence_family = bar_plot_dict(occurrences_df, "family", 2)
    occurrence_genus = bar_plot_dict(occurrences_df, "genus", 0.5)
    occurrence_taxonRank = bar_plot_dict(occurrences_df, "taxonRank", 2)
    occurrence_habitat1 = bar_plot_dict(occurrences_df, "habitat1", 0)
    occurrence_habitat2 = bar_plot_dict(occurrences_df, "habitat2", 1)

    # Taxa metrics
    scientificName = []
    taxa_taxonRank = []
    date = []
    taxa_order = []
    taxa_family = []
    for occ in occurrences:
        if occ.scientificName not in scientificName:
            scientificName.append(occ.scientificName)
            taxa_taxonRank.append(occ.taxonRank)
            taxa_order.append(occ.order)
            taxa_family.append(occ.family)
            date.append(occ.dateIdentified)
    
    taxa_dict = {
        "scientificName": scientificName, "order": taxa_order, "family": taxa_family, 
        "taxonRank": taxa_taxonRank, "date": date
    }
    taxa_df = pd.DataFrame(taxa_dict)
    
    # Taxa metrics - convert numpy arrays to lists
    taxa_year = bar_plot_dict(taxa_df, "year", 0)
    taxa_order = bar_plot_dict(taxa_df, "order", 1)
    taxa_family = bar_plot_dict(taxa_df, "family", 0.5)
    taxa_taxonRank = bar_plot_dict(taxa_df, "taxonRank", 1)
    
            
    # Taxa per method
    met_count = []
    for method in methods:
        taxa = []
        for occurrence in occurrences:
            if occurrence.samplingProtocol == method:
                if occurrence.scientificName not in taxa:
                    taxa.append(occurrence.scientificName)
        met_count.append(len(taxa))
    groups_df = pd.DataFrame({"count": met_count}, index=methods)
    groups_df = groups_df.sort_values(by=['count'])
    groups_df = groups_df[groups_df['count'] > 0]
    met_taxon_count = {"label": list(groups_df.index), "count": list(groups_df["count"])}
    
    # Counts
    taxa_len = len(scientificName)
    occ_len = len(occurrences)
    event_len = len(events)
    
    return {
        # Counts
        'occ_len': occ_len,
        'event_len': event_len,
        'taxa_len': taxa_len,

        # Events metrics - convert to lists
        'event_year': event_year,
        'event_month': event_month,
        'event_method': event_method,
        'event_habitat1': event_habitat1,
        'event_habitat2': event_habitat2,
        
        # Occurrences metrics - convert to lists
        'occurrence_year': occurrence_year,
        'occurrence_month': occurrence_month,
        'occurrence_method': occurrence_method,
        'occurrence_habitat1': occurrence_habitat1,
        'occurrence_habitat2': occurrence_habitat2,
        'occurrence_order': occurrence_order,
        'occurrence_family': occurrence_family,
        'occurrence_genus': occurrence_genus,
        'occurrence_taxonRank': occurrence_taxonRank,
        
        # Taxa metrics - convert to lists
        'met_taxon_count': met_taxon_count,
        'taxa_year': taxa_year,
        'taxa_taxonRank': taxa_taxonRank,
        'taxa_order': taxa_order,
        'taxa_family': taxa_family,
    }