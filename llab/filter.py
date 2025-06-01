# load packages
from .functions import bar_plot_dict
from flask import Blueprint, request, render_template, flash, request
from flask_login import login_required, current_user
from .models import Occurrences, Taxa, Identification_events, Collecting_events, Country_codes, Eunis_habitats, Datasets, Units, Drawers, co1, Observations
from . import db
import numpy as np
import pandas as pd
import json

# connect to __init__ file
filter = Blueprint('filter', __name__)

# Display specimen data on a map, as a table, and with metrics. The user can filter the data by scanning QR-codes, selecting taxa, localities, habitats, dates, methods, and datasets.
@filter.route('/', methods=["POST", "GET"])
@login_required 
def home():
    # Prepare lists for dropdown-select-search bar
    specimen_ids=[] # Initialize list for specimen-IDs
    collecting_events = Collecting_events.query.all() # Database query for collecting events
    event_ids = np.unique([i.eventID for i in collecting_events if i.eventID]) # Database query for event_ids
    methods = np.unique([i.samplingProtocol for i in collecting_events if i.samplingProtocol]) # Database query for sampling methods
    datasets = Datasets.query.all() # Database query for datasets
    drawers = [i.drawerName for i in Drawers.query.all()] # Database query for drawers
    taxa = Taxa.query.all() # Database query for taxa
    ranks = np.unique([i.taxonRank for i in taxa if i.taxonRank]) # Database query for taxon ranks
    country_codes = np.unique([i.countryCode for i in collecting_events if i.countryCode]) # Database query for country
    # Loop over country codes and get country names
    countries = [] # Initialize list for countries
    for i in country_codes:
        country = Country_codes.query.filter_by(countryCode=i).first()
        if country:
            countries.append(country.country)
    counties = np.unique([i.county for i in collecting_events if i.county]) # Database query for county
    municipalities = np.unique([i.municipality for i in collecting_events if i.municipality]) # Database query for municipality
    # Get Eunis habitats
    habitats = Eunis_habitats.query.all()
    habitat_level2 = []
    # Loop over habitats and get habitat level 2
    for habitat in habitats:
        if habitat.level2 not in habitat_level2:
            habitat_level2.append(habitat.level2)
    # Create  list of names and ranks for taxa-dropdown-select-search bar
    cl = tuple(np.unique([i.cl for i in taxa if i.cl]))
    order = tuple(np.unique([i.order for i in taxa if i.order]))
    family = tuple(np.unique([i.family for i in taxa if i.family]))
    genus = tuple(np.unique([i.genus for i in taxa if i.genus]))
    scientificName = tuple(np.unique([i.scientificName for i in taxa]))
    dropdown_names = cl+order+family+genus+scientificName
    dropdown_ranks = tuple(len(cl)*["class"]+len(order)*["order"]+len(family)*["family"]+len(genus)*[
                           "genus"]+len(scientificName)*["scientificName"])
    
    # FILTER SPECIMEN DATA
    # This filterering function first adds all specimen-IDs in the database to a specimen-list. Then, applies the filters, one by one, to the list of specimen-IDs. If any QR-codes (specimen-labels, unit-labels or drawer-labels) are scanned, the specimen-IDs from these are used as a starting pont of the specimen-list.
    if request.method == 'POST':
        if request.form.get('specimen_filter') == 'specimen_filter':
            # Use all specimen-IDs in the database as a starting point
            if request.form.get("occurrence_ids") or request.form.get("unit_ids") or request.form.get("drawer_name") or request.form.get("taxon_name") or request.form.get("taxon_rank") or request.form.get("sex") or request.form.get("eventID") or request.form.get("country") or request.form.get("county") or request.form.get("municipality") or request.form.get("eunis") or request.form.get("date_from") or request.form.get("date_to") or request.form.get("method") or request.form.get("datasetfilter"):
                specimen_ids = [i.occurrenceID for i in Occurrences.query.all()]
            # 8. QR filter. If any QR-codes are scanned, crete a specimen-list from these
            if request.form.get("occurrence_ids") or request.form.get("unit_ids") or request.form.get("drawer_name"):
                specimen_ids = []
                event_ids = [] # Empty list of event-IDs
                # 8.1 Specimen-label QR-codes 
                if request.form.get("occurrence_ids"):
                    specimen_QR_label = request.form.get("occurrence_ids")
                    specimen_QR_label = specimen_QR_label.splitlines()
                    specimen_QR_label = [i.replace("http://purl.org/nhmuio/id/", "") for i in specimen_QR_label]
                    specimen_ids = np.unique(specimen_ids+specimen_QR_label)
                # 8.2 Unit-label qr-codes
                if request.form.get("unit_ids"):
                    unit_QR_label = request.form.get("unit_ids")
                    unit_QR_label = unit_QR_label.splitlines()
                    unit_QR_label = Occurrences.query.filter(Occurrences.unit_id.in_(unit_QR_label))
                    unit_QR_label = [i.occurrenceID for i in unit_QR_label]
                    specimen_ids = np.unique(specimen_ids+unit_QR_label)
                # 8.3 Drawer-label qr-codes
                if request.form.get("drawer_name"):
                    drawer_QR_label = request.form.get("drawer_name")
                    drawer_QR_label = drawer_QR_label.splitlines()
                    drawer_QR_label = Occurrences.query.join(Units, Units.unitID==Occurrences.unit_id).join(Drawers, Units.drawerName==Drawers.drawerName).filter(Drawers.drawerName.in_(drawer_QR_label)).all()
                    drawer_QR_label = [i.occurrenceID for i in drawer_QR_label]
                    specimen_ids = np.unique(specimen_ids+drawer_QR_label)
            # 1. Taxon filter
            if request.form.get("taxon_name"):
                event_ids = [] # Empty list of event-IDs
                taxa = request.form.getlist("taxon_name")
                # Loop over selected taxa and get scientific names of (children) species
                scientific_names = list()
                for i in taxa:
                    taxon = i.split(";")
                    # Query occurrences of given taxon
                    if (taxon[1] == "scientificName"):
                        scientific_names_tmp = [taxon[0]]
                    else:
                        if (taxon[1] == "class"):
                            taxa_db = Taxa.query.filter_by(cl=taxon[0])
                        if (taxon[1] == "order"):
                            taxa_db = Taxa.query.filter_by(order=taxon[0])
                        if (taxon[1] == "family"):
                            taxa_db = Taxa.query.filter_by(family=taxon[0])
                        if (taxon[1] == "genus"):
                            taxa_db = Taxa.query.filter_by(genus=taxon[0])
                        scientific_names_tmp = [i.scientificName for i in taxa_db if i.scientificName]
                    scientific_names = scientific_names+list(scientific_names_tmp)
                scientific_names = np.unique(scientific_names)
                # Get occurrences for selected taxa
                taxon_fiter_occurrences = Occurrences.query\
                    .join(Identification_events, Occurrences.identificationID==Identification_events.identificationID)\
                    .with_entities(Occurrences.occurrenceID, Identification_events.scientificName)\
                    .filter(Identification_events.scientificName.in_(scientific_names))\
                    .all()
                taxon_fiter_occurrences = [i.occurrenceID for i in taxon_fiter_occurrences]
                # Apply taxon filter on starting point of specimen-list
                specimen_ids = np.intersect1d(specimen_ids, taxon_fiter_occurrences)
            # 2. Taxon rank filter
            if request.form.get("taxon_rank"):
                event_ids = [] # Empty list of event-IDs
                taxon_rank = request.form.get("taxon_rank")
                # Get occurrences for selected taxon rank
                rank_fiter_occurrences = Occurrences.query\
                    .join(Identification_events, Occurrences.identificationID==Identification_events.identificationID)\
                    .join(Taxa, Identification_events.scientificName==Taxa.scientificName)\
                    .filter_by(taxonRank=taxon_rank).all()
                rank_fiter_occurrences = [i.occurrenceID for i in rank_fiter_occurrences]
                specimen_ids = np.intersect1d(specimen_ids, rank_fiter_occurrences)
            # 3. Sex filter
            if request.form.get("sex"):
                event_ids = [] # Empty list of event-IDs
                sex = request.form.get("sex")
                # Get occurrences for selected sex
                sex_fiter_occurrences = Occurrences.query\
                    .join(Identification_events, Occurrences.identificationID==Identification_events.identificationID)\
                    .filter_by(sex=sex).all()
                sex_fiter_occurrences = [i.occurrenceID for i in sex_fiter_occurrences]
                specimen_ids = np.intersect1d(specimen_ids, sex_fiter_occurrences)
            # 4. Collecting event ID filter
            if request.form.get("eventID"):
                eventID = request.form.get("eventID")
                # Get occurrences for selected eventID
                event_fiter_occurrences = Occurrences.query\
                    .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
                    .filter_by(eventID=eventID).all()
                event_fiter_occurrences = [i.occurrenceID for i in event_fiter_occurrences]
                specimen_ids = np.intersect1d(specimen_ids, event_fiter_occurrences)
                # Add eventID to eventIDs list
                event_ids = eventID
            # 4. Locality filter
            if request.form.get("country") or request.form.get("county") or request.form.get("municipality"):                
                # 4.3 Municipality. If municipality is selected, forget about country and county
                if request.form.get("municipality"):
                    municipality = request.form.get("municipality")
                    locality_fiter_occurrences = Occurrences.query\
                        .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
                        .filter_by(municipality=municipality).all()
                    # Get eventIDs
                    locality_filter_eventIDs = Collecting_events.query.filter_by(municipality=municipality).all()
                # 4.2 County. If county is selected, forget about country
                elif request.form.get("county"):
                    county = request.form.get("county")
                    locality_fiter_occurrences = Occurrences.query\
                        .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
                        .filter_by(county=county).all()
                    # Get eventIDs
                    locality_filter_eventIDs = Collecting_events.query.filter_by(county=county).all()
                # 4.1 Country
                else:
                    country = request.form.get("country")
                    locality_fiter_occurrences = Occurrences.query\
                        .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
                        .join(Country_codes, Collecting_events.countryCode==Country_codes.countryCode)\
                        .filter(Country_codes.country==country).all()
                    # Get eventIDs
                    locality_filter_eventIDs = Collecting_events.query.join(Country_codes, Collecting_events.countryCode==Country_codes.countryCode).filter(Country_codes.country==country).all()
                locality_fiter_occurrences = [i.occurrenceID for i in locality_fiter_occurrences]
                specimen_ids = np.intersect1d(specimen_ids, locality_fiter_occurrences)
                # Add eventIDs to eventIDs list
                event_ids = np.intersect1d([i.eventID for i in locality_filter_eventIDs], event_ids)
            # 5. Habitat
            if request.form.get("eunis"):
                habitat = request.form.get("eunis")
                if Eunis_habitats.query.filter_by(level1=habitat).first():
                    habitat_fiter_occurrences = Occurrences.query\
                        .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
                        .join(Eunis_habitats, Collecting_events.eunisCode==Eunis_habitats.eunisCode)\
                        .filter_by(level1=habitat).all()
                    # Get eventIDs
                    habitat_filter_eventIDs = Collecting_events.query.join(Eunis_habitats, Collecting_events.eunisCode==Eunis_habitats.eunisCode).filter_by(level1=habitat).all()
                elif Eunis_habitats.query.filter_by(level2=habitat).first():
                    habitat_fiter_occurrences = Occurrences.query\
                        .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
                        .join(Eunis_habitats, Collecting_events.eunisCode==Eunis_habitats.eunisCode)\
                        .filter_by(level2=habitat).all()
                    # Get eventIDs
                    habitat_filter_eventIDs = Collecting_events.query.join(Eunis_habitats, Collecting_events.eunisCode==Eunis_habitats.eunisCode).filter_by(level2=habitat).all()
                else:
                    habitat_fiter_occurrences = Occurrences.query\
                        .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
                        .join(Eunis_habitats, Collecting_events.eunisCode==Eunis_habitats.eunisCode)\
                        .filter_by(eunisCode=habitat).all()
                    # Get eventIDs
                    habitat_filter_eventIDs = Collecting_events.query.join(Eunis_habitats, Collecting_events.eunisCode==Eunis_habitats.eunisCode).filter_by(eunisCode=habitat).all()
                habitat_fiter_occurrences = [i.occurrenceID for i in habitat_fiter_occurrences]
                specimen_ids = np.intersect1d(specimen_ids, habitat_fiter_occurrences)
                # Add eventIDs to eventIDs list
                event_ids = np.intersect1d([i.eventID for i in habitat_filter_eventIDs], event_ids)
            # 6. Date
            if request.form.get("date_from"):
                date_from = request.form.get("date_from")
                date_to = request.form.get("date_to")
                date_fiter_occurrences = Occurrences.query\
                    .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
                    .filter(Collecting_events.eventDate_1>=date_from, Collecting_events.eventDate_1<=date_to).all()
                date_fiter_occurrences = [i.occurrenceID for i in date_fiter_occurrences]
                specimen_ids = np.intersect1d(specimen_ids, date_fiter_occurrences)
                # Add eventIDs to eventIDs list
                date_filter_eventIDs = Collecting_events.query.filter(Collecting_events.eventDate_1>=date_from, Collecting_events.eventDate_1<=date_to).all()
                event_ids = np.intersect1d([i.eventID for i in date_filter_eventIDs], event_ids)
            # 7. Method
            if request.form.get("method"):
                method = request.form.get("method")
                method_fiter_occurrences = Occurrences.query\
                    .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID)\
                    .filter_by(samplingProtocol=method).all()
                method_fiter_occurrences = [i.occurrenceID for i in method_fiter_occurrences]
                specimen_ids = np.intersect1d(specimen_ids, method_fiter_occurrences)
                # Add eventIDs to eventIDs list
                method_fiter_eventIDs = Collecting_events.query.filter_by(samplingProtocol=method).all()
                event_ids = np.intersect1d([i.eventID for i in method_fiter_eventIDs], event_ids)
            # 9. Dataset
            if request.form.get("datasetfilter"):
                dataset = request.form.get("datasetfilter")
                dataset_fiter_occurrences = Datasets.query.filter_by(datasetName=dataset).first()
                # The occurrences in the dataset are formatted as a string delimited by " | ". Split the string and convert to list.
                dataset_fiter_occurrences = dataset_fiter_occurrences.specimenIDs.split(" | ")
                specimen_ids = np.intersect1d(specimen_ids, dataset_fiter_occurrences)
                # Add eventIDs to eventIDs list. THIS MAY CAUSE BUGS!!!
                dataset_filter_occurrences = Occurrences.query.filter(Occurrences.occurrenceID.in_(dataset_fiter_occurrences))
                dataset_filter_eventIDs = [i.eventID for i in dataset_filter_occurrences]
                dataset_filter_eventIDs = np.unique(dataset_filter_eventIDs)
                event_ids = np.intersect1d(dataset_filter_eventIDs, event_ids)        
        # If requested, get event-id from show_event.html
        if request.form.get("collecting_event_id") == "collecting_event_id":
            eventID = request.form.get("eventID")
            event = Collecting_events.query.filter_by(eventID=eventID).first()
            specimen_ids = [i.occurrenceID for i in event.occurrences]
            event_ids = [eventID]
    # Get occurrences for filtered specimen-IDs
    occurrences = Occurrences.query.filter(Occurrences.occurrenceID.in_(specimen_ids))\
            .join(Identification_events, Occurrences.identificationID==Identification_events.identificationID, isouter=True)\
            .join(Taxa, Identification_events.scientificName==Taxa.scientificName, isouter=True)\
            .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID, isouter=True)\
            .join(Country_codes, Collecting_events.countryCode==Country_codes.countryCode, isouter=True)\
            .join(Eunis_habitats, Collecting_events.eunisCode==Eunis_habitats.eunisCode, isouter=True)\
            .join(co1, Occurrences.occurrenceID==co1.occurrenceID, isouter=True)\
            .with_entities(Occurrences.occurrenceID, Country_codes.country, Collecting_events.eventID,
            Collecting_events.municipality, Collecting_events.locality_1, Collecting_events.locality_2, 
            Collecting_events.habitat, Collecting_events.substrateName, Collecting_events.substratePlantPart, 
            Collecting_events.substrateType, Collecting_events.eventDate_1, Collecting_events.eventDate_2, 
            Collecting_events.samplingProtocol, Collecting_events.recordedBy, Taxa.scientificName, Taxa.genus, Taxa.family, 
            Taxa.order, Taxa.taxonRank, Taxa.scientificNameAuthorship, Identification_events.identifiedBy, 
            Identification_events.dateIdentified, Identification_events.identificationQualifier, Identification_events.sex, 
            Eunis_habitats.level1, Eunis_habitats.level2, Eunis_habitats.habitatName, Eunis_habitats.eunisCode, co1.sequenceID)\
            .order_by(Taxa.scientificName, Collecting_events.eventID)\
            .all()
    
    # METRICS
    # 1. Collecting_events
    # If filter is applied, get updated event_ids
    #event_ids = np.ndarray.tolist(event_ids)
    event_ids = list(event_ids)
    if request.method == 'POST':
        # Get unique eventIDs
        #event_ids = []
        for occurrence in occurrences:
            if occurrence.eventID not in event_ids:
                event_ids.append(occurrence.eventID)
    # Get event data
    events = Collecting_events.query.filter(Collecting_events.eventID.in_(event_ids))\
        .join(Eunis_habitats, Collecting_events.eunisCode==Eunis_habitats.eunisCode, isouter=True)\
        .with_entities(Collecting_events.eventID, Collecting_events.decimalLatitude, Collecting_events.decimalLongitude, Collecting_events.samplingProtocol, Collecting_events.eventDate_1, Eunis_habitats.level1, Eunis_habitats.level2)\
        .all()
    # Count events
    event_len = len(events)
    # Create Eunis habitats dictionary
    eunis_dict = {}
    for i in habitats:
        eunis_dict[i.eunisCode] = i.habitatName
    # Create dataframe
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
    # Yearly
    event_year = bar_plot_dict(events_df, "year", 0)
    # Monthly
    event_month = bar_plot_dict(events_df, "month", 0)
    # Methods
    event_method = bar_plot_dict(events_df, "samplingProtocol", 0)
    # Habitat level 1
    event_habitat1 = bar_plot_dict(events_df, "habitat1", 0)
    # Habitat level 2
    event_habitat2 = bar_plot_dict(events_df, "habitat2", 1)
    
    # 2. Occurrences
    # Create dataframe
    family = []
    order = []
    genus = []
    taxonRank = []
    samplingProtocol = []
    eventDate_1 = []
    habitat1 = []
    habitat2 = []
    for row in occurrences:
        family.append(row.family)
        order.append(row.order)
        genus.append(row.genus)
        taxonRank.append(row.taxonRank)
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
    occurrences_dict = {"family":family, "order":order, "genus":genus, "taxonRank":taxonRank,"samplingProtocol":samplingProtocol, "date":eventDate_1, "habitat1":habitat1, "habitat2":habitat2}
    occurrences_df = pd.DataFrame(occurrences_dict)
    # Yearly
    occurrence_year = bar_plot_dict(occurrences_df, "year", 0)
    # Monthly
    occurrence_month = bar_plot_dict(occurrences_df, "month", 0)
    # Method
    occurrence_method = bar_plot_dict(occurrences_df, "samplingProtocol", 0)
    # Order
    occurrence_order = bar_plot_dict(occurrences_df, "order", 1)
    # Family
    occurrence_family = bar_plot_dict(occurrences_df, "family", 2)
    # Genus
    occurrence_genus = bar_plot_dict(occurrences_df, "genus", 0.5)
    # Rank
    occurrence_taxonRank = bar_plot_dict(occurrences_df, "taxonRank", 2)
    # Habitat level 1
    occurrence_habitat1 = bar_plot_dict(occurrences_df, "habitat1", 0)
    # Habitat level 2
    occurrence_habitat2 = bar_plot_dict(occurrences_df, "habitat2", 1)

    # 3. Taxa
    # Create dataframe
    scientificName = []
    taxonRank = []
    date = []
    order = []
    family = []
    index = 1
    for i in occurrences:
        if i.scientificName not in scientificName:
            index+=1
            scientificName.append(i.scientificName)
            taxonRank.append(i.taxonRank)
            order.append(i.order)
            family.append(i.family)
            date.append(i.dateIdentified)
    taxa_dict = {"scientificName":scientificName, "order":order, "family":family, "taxonRank":taxonRank, "date":date}
    
    taxa_df = pd.DataFrame(taxa_dict)
    # Yearly
    taxa_year = bar_plot_dict(taxa_df, "year", 0)
    # Order
    taxa_order = bar_plot_dict(taxa_df, "order", 1)
    # Family
    taxa_family = bar_plot_dict(taxa_df, "family", 0.5)
    # Rank
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
    groups_df = pd.DataFrame({"count":met_count}, index=methods)
    groups_df = groups_df.sort_values(by=['count'])
    groups_df = groups_df[groups_df['count']>0]
    met_taxon_count = {"label":list(groups_df.index), "count":list(groups_df["count"])}
    # Taxa per habitat
    # Create dataframe
    #dateIdentified = []
    #for row in identification:
    #    dateIdentified.append(row.dateIdentified)
    #identification = {"date":dateIdentified}
    #identification_df = pd.DataFrame(identification)
    # Yearly
    #identification_year = bar_plot_dict(identification_df, "year", 0)
    # Count taxa, events and occurrences
    taxa_len = len(taxa_df)
    occ_len = len(occurrences)
    event_len = len(events)
    # Report if any of the specified occurrenceIDs are not present in database.
    for occurrence in specimen_ids:
        if occurrence not in [i.occurrenceID for i in occurrences]:
            flash(f'{occurrence} not in database', category="error")
    # Return template
    return render_template("home.html", user=current_user, habitats=habitats, habitat_level2=habitat_level2, countries=countries, counties=counties, municipalities=municipalities, methods=methods, collecting_events=collecting_events, datasets=datasets, dropdown_names=dropdown_names, dropdown_ranks=dropdown_ranks, occurrences=occurrences, events=events, ranks=ranks, occ_len=occ_len, event_len=event_len, taxa_len=taxa_len, occurrence_year=occurrence_year, occurrence_month=occurrence_month, occurrence_method=occurrence_method, occurrence_habitat1=occurrence_habitat1, occurrence_habitat2=occurrence_habitat2, occurrence_order=occurrence_order, occurrence_family=occurrence_family, occurrence_genus=occurrence_genus, occurrence_taxonRank=occurrence_taxonRank, met_taxon_count=met_taxon_count, taxa_year=taxa_year, taxa_taxonRank=taxa_taxonRank, taxa_order=taxa_order, taxa_family=taxa_family, event_year = event_year, event_month = event_month, event_method = event_method, event_habitat1 = event_habitat1, event_habitat2 = event_habitat2, drawers=drawers, event_ids=event_ids)

