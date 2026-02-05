# Flask module for handling datasets
from flask import Blueprint, current_app, redirect, url_for, render_template, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from .models import User, Collecting_events, Occurrences, Observations, Country_codes, Eunis_habitats, Identification_events, Taxa, Chalcidoidea, co1, Sequence_alignment, Collectors, Datasets
from . import db
import numpy as np
import pandas as pd
import csv
from .filters import locality_format, format_dates3, format_substrate
from .functions import format_occurrence_block, format_biology_block, format_distribution_block, number_of_individuals, format_new_distribution, format_gbif_date
from collections import defaultdict
from Bio import SeqIO
import subprocess
import os
from tempfile import NamedTemporaryFile
from werkzeug.utils import secure_filename

# connect to __init__ file
export = Blueprint('export', __name__)

# Specify app
app = current_app
    
@export.route('/export_events/<string:eventIDs>', methods=["GET"])
@login_required
def export_events(eventIDs):
    # Check if eventIDs are provided
    if not eventIDs:
        return "No collecting-event IDs provided", 400
    # 
    try:
        event_ids = eventIDs.split("|")
        if not event_ids:
            return "No valid event IDs provided", 400
        # Query event data
        events = Collecting_events.query.filter(Collecting_events.eventID.in_(event_ids)).all() # Get the dataset
        if not events:
            return "No matching collecting-events found", 404
        # Format a list for export
        header = ["CollectingEventID", "CountryCode", "State/Province", "County", "Municipality", "Locality", "Habitat", "DecimalDeg", "googleMapsLink", "Radius", "SamplingProtocol", "eventDate1", "eventDate2", "recordedBy", "Remarks", "databased"]
        # Create a temporary file
        temp_file = NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8')
        try:
            writer = csv.writer(temp_file)
            writer.writerow(header)
            for event in events:
                row = [event.eventID, event.countryCode, event.stateProvince, event.county, event.municipality, locality_format(event.locality_1, event.locality_2), event.habitat, f'{event.decimalLatitude}, {event.decimalLongitude}', f"http://maps.google.com/maps?q={event.decimalLatitude},{event.decimalLongitude}", event.coordinateUncertaintyInMeters, event.samplingProtocol, event.eventDate_1, event.eventDate_2, event.recordedBy, event.eventRemarks, event.databased]
                writer.writerow(row)
            temp_file.close()

            return send_file(
                temp_file.name,
                mimetype='text/csv',
                download_name='event_export.csv',
                as_attachment=True
            )
        except Exception as e:
            temp_file.close()
            os.unlink(temp_file.name)
            raise e

    except Exception as e:
        return f"An error occurred: {str(e)}", 500    
            

@export.route('/export_GBIF', methods=["GET"])
@login_required
def export_GBIF():
    occurrenceIDs = request.args.get("specimen_ids")
    if not occurrenceIDs:
        return "No occurrence IDs provided", 400

    try:
        specimen_ids = occurrenceIDs.split("|")
        if not specimen_ids:
            return "No valid occurrence IDs provided", 400

        # Query occurrences
        occurrences = (
            Occurrences.query.filter(Occurrences.occurrenceID.in_(specimen_ids))
            .join(Identification_events, Occurrences.identificationID == Identification_events.identificationID, isouter=True)
            .join(Taxa, Identification_events.scientificName == Taxa.scientificName, isouter=True)
            .join(Collecting_events, Occurrences.eventID == Collecting_events.eventID, isouter=True)
            .with_entities(
                Occurrences.ownerInstitutionCode,
                Occurrences.catalogNumber,
                Occurrences.occurrenceID,
                Collecting_events.eventDate_1,
                Collecting_events.eventDate_2,
                Taxa.scientificName,
                Taxa.scientificNameAuthorship,
                Taxa.taxonRank,
                Taxa.order,
                Taxa.family,
                Taxa.genus,
                Taxa.specificEpithet,
                Identification_events.lifeStage,
                Identification_events.sex,
                Collecting_events.locality_1,
                Collecting_events.locality_2,
                Collecting_events.decimalLatitude,
                Collecting_events.decimalLongitude,
                Collecting_events.coordinateUncertaintyInMeters,
                Collecting_events.eventID,
                Collecting_events.geodeticDatum,
                Collecting_events.countryCode,
                Collecting_events.county,
                Collecting_events.stateProvince,
                Collecting_events.recordedBy,
                Identification_events.identifiedBy,
                Identification_events.dateIdentified,
                Occurrences.preparations,
                Occurrences.individualCount,
                Occurrences.associatedTaxa,
                Collecting_events.samplingProtocol,
                Occurrences.occurrenceRemarks,
                Occurrences.associatedReferences,
                Collecting_events.eventRemarks,
                Collecting_events.substrateName,
                Collecting_events.substratePlantPart,
                Collecting_events.substrateType,
                Collecting_events.municipality,
                Collecting_events.habitat
            )
            .order_by(Taxa.scientificName, Collecting_events.eventID)
            .all()
        )

        if not occurrences:
            return "No matching occurrences found", 404

        header = ["institutionCode", "catalogNumber", "occurrenceID", "basisOfRecord", "eventDate", "scientificName", "scientificNameAuthorship", "taxonRank", "order", "family", "genus", "specificEpithet", "lifeStage", "sex", "locality", "decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters", "eventID", "geodeticDatum", "countryCode", "county", "stateProvince", "municipality", "habitat", "recordedBy", "recordedByID", "identifiedBy", "identifiedByID", "dateIdentified", "preparations", "individualCount", "associatedTaxa", "samplingProtocol", "occurrenceRemarks", "associatedReferences", "fieldNotes", "license"]

        # Create a temporary file
        temp_file = NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8')
        try:
            writer = csv.writer(temp_file)
            writer.writerow(header)

            for occurrence in occurrences:
                # Handle remarks
                remarks = occurrence.occurrenceRemarks
                if occurrence.substrateName:
                    substrate_remarks = format_substrate(
                        occurrence.substrateName, 
                        occurrence.substratePlantPart, 
                        occurrence.substrateType
                    )
                    remarks = f"{substrate_remarks} | {remarks}" if remarks else substrate_remarks

                # Safely get collector IDs
                recordedByID = ""
                if occurrence.recordedBy:
                    collector = Collectors.query.filter(
                        Collectors.recordedBy.in_(occurrence.recordedBy.split(" | "))
                    ).with_entities(Collectors.recordedByID).all()
                    print(collector)                       
                    recordedByID = " | ".join([i.recordedByID for i in collector]) if collector else ""

                identifiedByID = ""
                if occurrence.identifiedBy:
                    identifier = Collectors.query.filter(
                         Collectors.recordedBy.in_(occurrence.identifiedBy.split(" | "))
                    ).with_entities(Collectors.recordedByID).all()
                    print(identifier)
                    identifiedByID = " | ".join(i.recordedByID for i in identifier) if identifier else ""


                row = [occurrence.ownerInstitutionCode, occurrence.catalogNumber, occurrence.occurrenceID, "PreservedSpecimen", format_dates3(occurrence.eventDate_1, occurrence.eventDate_2), occurrence.scientificName, occurrence.scientificNameAuthorship, occurrence.taxonRank, occurrence.order, occurrence.family, occurrence.genus, occurrence.specificEpithet, occurrence.lifeStage, occurrence.sex, locality_format(occurrence.locality_1, occurrence.locality_2), occurrence.decimalLatitude, occurrence.decimalLongitude, occurrence.coordinateUncertaintyInMeters, occurrence.eventID, occurrence.geodeticDatum, occurrence.countryCode, occurrence.county, occurrence.stateProvince, occurrence.municipality, occurrence.habitat, occurrence.recordedBy, recordedByID, occurrence.identifiedBy, identifiedByID, occurrence.dateIdentified, occurrence.preparations, occurrence.individualCount, occurrence.associatedTaxa, occurrence.samplingProtocol, remarks, occurrence.associatedReferences, occurrence.eventRemarks, "http://creativecommons.org/licenses/by/4.0/legalcode"]

                writer.writerow(row)

            temp_file.close()

            return send_file(
                temp_file.name,
                mimetype='text/csv',
                download_name='gbif_export.csv',
                as_attachment=True
            )
        except Exception as e:
            temp_file.close()
            os.unlink(temp_file.name)
            raise e

    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@export.route('/export_faunistic_report', methods=["GET"])
@login_required
def export_faunistic_report():
    occurrenceIDs = request.args.get("specimen_ids")
    if not occurrenceIDs:  # Validate occurrenceIDs
        return "No occurrence IDs provided", 400
    
    # Split occurrenceIDs into a list
    specimen_ids = occurrenceIDs.split("|")
    
    # Get occurrence data from the database
    occurrences = (
        Occurrences.query.filter(Occurrences.occurrenceID.in_(specimen_ids))
        .join(
            Identification_events,
            Occurrences.identificationID == Identification_events.identificationID,
            isouter=True
        )
        .join(
            Taxa,
            Identification_events.scientificName == Taxa.scientificName,
            isouter=True
        )
        .join(
            Collecting_events,
            Occurrences.eventID == Collecting_events.eventID,
            isouter=True
        )
        .join(
            Country_codes,
            Collecting_events.countryCode == Country_codes.countryCode,
            isouter=True
        )
        .join(
            Eunis_habitats,
            Collecting_events.eunisCode == Eunis_habitats.eunisCode,
            isouter=True
        )
        .with_entities(
            Occurrences.occurrenceID,
            Occurrences.catalogNumber,
            Occurrences.ownerInstitutionCode,
            Occurrences.individualCount,
            Occurrences.associatedTaxa,
            Country_codes.country,
            Collecting_events.eventID,
            Collecting_events.stateProvince,
            Collecting_events.county,
            Collecting_events.strand_id,
            Collecting_events.municipality,
            Collecting_events.locality_1,
            Collecting_events.locality_2,
            Collecting_events.habitat,
            Collecting_events.samplingProtocol,
            Collecting_events.substrateName,
            Collecting_events.substratePlantPart,
            Collecting_events.substrateType,
            Collecting_events.eventDate_1,
            Collecting_events.eventDate_2,
            Collecting_events.samplingProtocol,
            Collecting_events.recordedBy,
            Taxa.scientificName,
            Taxa.genus,
            Taxa.family,
            Taxa.order,
            Taxa.taxonRank,
            Taxa.scientificNameAuthorship,
            Identification_events.identifiedBy,
            Identification_events.dateIdentified,
            Identification_events.identificationQualifier,
            Identification_events.sex,
            Eunis_habitats.level1,
            Eunis_habitats.level2,
            Eunis_habitats.habitatName,
            Eunis_habitats.eunisCode,
        )
        .order_by(Taxa.scientificName, Collecting_events.eventID)
        .all()
    )

    # Convert the SQLAlchemy row objects into a dictionary keyed by occurrenceID
    occurrences_dict = {}
    for occ in occurrences:
        occurrences_dict[occ.occurrenceID] = {
        "catalogNumber": occ.catalogNumber,
        "scientificName": occ.scientificName,
        "sex": occ.sex,
        "individualCount": occ.individualCount,
        "occurrenceID": occ.occurrenceID,
        "country": occ.country,
        "stateProvince": occ.stateProvince,
        "samplingProtocol": occ.samplingProtocol,
        "habitat": occ.habitat,
        "substrateName": occ.substrateName,
        "substratePlantPart": occ.substratePlantPart,
        "substrateType": occ.substrateType,
        "associatedTaxa": occ.associatedTaxa,
        "county": occ.county,  
        "strand_id": occ.strand_id, 
        "municipality": occ.municipality,
        "locality_1": occ.locality_1,
        "locality_2": occ.locality_2,
        "eventDate_1": occ.eventDate_1,
        "eventDate_2": occ.eventDate_2,
        "recordedBy": occ.recordedBy,
        "ownerInstitutionCode": occ.ownerInstitutionCode,
        "order": getattr(occ, 'order', None),
        "family": getattr(occ, 'family', None),
        # add any other fields you need
        }
    
    # Create hierarchy of taxa
    orders = []
    families = []
    scientific_names = []

    for occurrence in occurrences:
        # Ensure attributes are not None
        if occurrence.taxonRank and occurrence.taxonRank != "class":
            if occurrence.order and occurrence.order not in orders:
                orders.append(occurrence.order)
            if occurrence.taxonRank != "order" and occurrence.family:
                if occurrence.family not in families:
                    families.append(occurrence.family)
                if occurrence.taxonRank != "family" and occurrence.scientificName:
                    if occurrence.scientificName not in scientific_names:
                        scientific_names.append(occurrence.scientificName)
    
    # Create hierarchy for Chalcid taxa
    chalcids = Chalcidoidea.query.all()
    chalcid_dict = {}
    for occurrence in occurrences:
        for chalcid in chalcids:
            if occurrence.scientificName.split(" ")[0] == chalcid.name:
                # Add species, species-group, sp-nov ranks
                if occurrence.taxonRank == "species" or occurrence.taxonRank == "genus" or occurrence.taxonRank == "species-group" or occurrence.taxonRank == "spnov" or occurrence.taxonRank == "other":
                    tmp_chalcid_name = occurrence.scientificName
                    tmp_rank = occurrence.taxonRank
                else:
                    tmp_chalcid_name = chalcid.name
                    tmp_rank = chalcid.rank
                chalcid_dict[occurrence.occurrenceID] = {
                    "chalcid_name": tmp_chalcid_name,
                    "chalcid_rank": tmp_rank,
                    "chalcid_fam": chalcid.family,
                    "chalcid_subfam": chalcid.subfamily,
                    "chalcid_tribe": chalcid.tribe
                }

    chalcid_hierarchy = {}

    for specimen_id, data in chalcid_dict.items():
        family     = data.get('chalcid_fam', '') or "<i>Incertae sedis</i> (Family)"
        subfamily  = data.get('chalcid_subfam', '') or "<i>Incertae sedis</i> (Subfamily)"
        tribe      = data.get('chalcid_tribe', '') or "<i>Incertae sedis</i> (Tribe)"
        genus_name = data.get('chalcid_name', '') or "<i>Incertae sedis</i> (Genus)"
        rank       = data.get('chalcid_rank', '')

        # Adjust levels according to rank
        if rank == "Family":
            # This specimen is identified ONLY to family
            # so override subfamily/tribe/genus as placeholders
            subfamily  = "0" #"No Subfamily"
            tribe      = "0" #"No Tribe"
            genus_name = "0" #"No Genus"

        elif rank == "Subfamily":
            # This specimen is identified ONLY to subfamily
            tribe      = "0" #"No Tribe"
            genus_name = "0" #"No Genus"

        elif rank == "Tribe":
            # Identified only to tribe
            genus_name = "0" #"No Genus"
        
        elif rank == "Genus":
            # Already has valid genus_name
            pass
        else:
            # If there's some other rank or missing info,
            # you can define a fallback behavior here.
            pass

        # Build up the dictionary
        # We do nested .setdefault(...) calls
        if family not in chalcid_hierarchy:
            chalcid_hierarchy[family] = {}
        if subfamily not in chalcid_hierarchy[family]:
            chalcid_hierarchy[family][subfamily] = {}
        if tribe not in chalcid_hierarchy[family][subfamily]:
            chalcid_hierarchy[family][subfamily][tribe] = {}
        chalcid_hierarchy[family][subfamily][tribe].setdefault(genus_name, []).append(specimen_id)

    def sort_hierarchy(hierarchy):
        if isinstance(hierarchy, dict):
            # Sort the dictionary keys and recursively sort the nested dictionaries
            return {key: sort_hierarchy(value) for key, value in sorted(hierarchy.items())}
        elif isinstance(hierarchy, list):
            # Sort lists (e.g., specimen_id lists)
            return sorted(hierarchy)
        else:
            return hierarchy

    # Apply the sorting function
    chalcid_hierarchy = sort_hierarchy(chalcid_hierarchy)

    # Render the template
    return render_template(
        "faunistic_report.html",
        occurrences_dict=occurrences_dict,
        chalcid_hierarchy=chalcid_hierarchy,
        format_occurrence_block=format_occurrence_block, # Pass the functions
        format_biology_block=format_biology_block,
        format_distribution_block=format_distribution_block,
        number_of_individuals=number_of_individuals,
        format_new_distribution=format_new_distribution,
        occurrences=occurrences,
        scientific_names=scientific_names,
        families=families,
        orders=orders,
    )

@export.route('/export_DNA_barcodes', methods=["GET"])
@login_required
def export_DNA_barcodes():
    occurrenceIDs = request.args.get("specimen_ids")
    if not occurrenceIDs:  # Validate occurrenceIDs
        return "No occurrence IDs provided", 400
    # Split occurrenceIDs into a list
    specimen_ids = occurrenceIDs.split("|")
    # Get DNA-barcodes    
    dna_barcodes = co1.query.filter(co1.occurrenceID.in_(specimen_ids)).all()
    
    ## Create alignment 
    # Write data to file in fasta-format
    output_fasta = "output.fasta"
    with open(output_fasta, "w") as fasta_file:
        for barcode in dna_barcodes:
            if barcode.sequenceID:
                tmp_name = f">{barcode.sequenceID}\n"
                fasta_file.write(tmp_name)
                fasta_file.write(f"{barcode.sequence}\n")
    
    # Run mafft --adjustdirection and mafft-linsi from terminal
    # Run first command and wait for it to finish
    p1 = subprocess.Popen('mafft --adjustdirection output.fasta > output.adjustdirection.fasta', shell=True)
    p1.wait()

    # Run second command
    p2 = subprocess.Popen('mafft-linsi output.adjustdirection.fasta > output.linsi.fasta', shell=True)
    p2.wait()
    
    # Delete previously aligned sequences in Sequence_alignment table
    Sequence_alignment.query.filter_by(createdByUserID=current_user.id).delete()
    db.session.commit()

    # Import aligned sequences and add them to Sequence_alignement table
    fasta_aligned = SeqIO.parse(open("output.linsi.fasta"),'fasta')
    for fasta in fasta_aligned:
        sequence_to_add = Sequence_alignment(sequenceID = fasta.id, sequence = fasta.seq, createdByUserID = current_user.id)
        db.session.add(sequence_to_add)
        db.session.commit()
    

    # Query aligned sequences with scientific names, occurrenceIDs and other parameters
    output_alignment = Sequence_alignment.query.filter_by(createdByUserID=current_user.id)\
        .join(co1, Sequence_alignment.sequenceID==co1.sequenceID, isouter=True)\
        .join(Occurrences, co1.occurrenceID==Occurrences.occurrenceID, isouter=True)\
        .join(Collecting_events, Occurrences.eventID==Collecting_events.eventID, isouter=True)\
        .join(Identification_events, Occurrences.identificationID==Identification_events.identificationID, isouter=True)\
        .join(Taxa, Identification_events.scientificName==Taxa.scientificName, isouter=True)\
        .with_entities(Occurrences.occurrenceID, Occurrences.associatedTaxa, Collecting_events.eventID, 
        Collecting_events.substrateName, Collecting_events.substratePlantPart, Collecting_events.substrateType, 
        Collecting_events.eunisCode, Taxa.scientificName, Identification_events.sex, Sequence_alignment.sequence, 
        Sequence_alignment.sequenceID)\
        .all()
    
    return render_template(
        "dna_barcodes.html",
        output_alignment = output_alignment
        )


####
# Export observations to a csv-file ready for GBIF import
####
@export.route('/export_observations_GBIF', methods=["GET"])
@login_required
def export_observations_GBIF():
    occurrenceIDs = request.args.get("specimen_ids")
    if not occurrenceIDs:
        return "No occurrence IDs provided", 400

    try:
        occurrence_ids = occurrenceIDs.split("|")
        if not occurrence_ids:
            return "No valid occurrence IDs provided", 400

        # Query observations
        observations = (
            Observations.query.filter(Observations.occurrenceID.in_(occurrence_ids))
            .join(Taxa, Observations.taxonInt == Taxa.taxonInt, isouter=True)
            .with_entities(
                Observations.occurrenceID,
                Observations.eventDateTime,
                Taxa.scientificName,
                Taxa.scientificNameAuthorship,
                Taxa.taxonRank,
                Taxa.order,
                Taxa.family,
                Taxa.genus,
                Taxa.specificEpithet,
                Observations.lifeStage,
                Observations.sex,
                Observations.locality,
                Observations.decimalLatitude,
                Observations.decimalLongitude,
                Observations.coordinateUncertaintyInMeters,
                Observations.countryCode,
                Observations.county,
                Observations.recordedBy,
                Observations.identifiedBy,
                Observations.dateIdentified,
                Observations.individualCount,
                Observations.occurrenceRemarks,
                Observations.imageFileNames,
                Observations.municipality
            )
            .order_by(Taxa.order, Taxa.family, Taxa.scientificName)
            .all()
        )

        if not observations:
            return "No matching observations found", 404

        header = ["ownerInstitutionCode",
        "basisOfRecord", 
        "occurrenceID",
        "eventDate",
        "scientificName",
        "taxonRank",
        "order",
        "family",
        "genus",
        "specificEpithet",
        "scientificNameAuthorship",
        "lifeStage",
        "sex",
        "individualCount",
        "decimalLatitude",
        "decimalLongitude",
        "coordinateUncertaintyInMeters",
        "countryCode",
        "county",
        "municipality",
        "locality",
        "recordedBy",
        "recordedByID",
        "identifiedBy",
        "identifiedByID",
        "dateIdentified",
        "occurrenceRemarks",
        "imageFileNames",
        ]
        
        # Create a temporary file
        temp_file = NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8')
        try:
            writer = csv.writer(temp_file)
            writer.writerow(header)

            for observation in observations:
                # Safely get collector IDs
                recordedByID = ""
                if observation.recordedBy:
                    collector = Collectors.query.filter(
                        Collectors.recordedBy == observation.recordedBy
                    ).with_entities(Collectors.recordedByID).first()
                    recordedByID = collector[0] if collector else ""

                identifiedByID = ""
                if observation.identifiedBy:
                    identifier = Collectors.query.filter(
                        Collectors.recordedBy == observation.identifiedBy
                    ).with_entities(Collectors.recordedByID).first()
                    identifiedByID = identifier[0] if identifier else ""

                row = ["TMU",
                    "HumanObservation", 
                    observation.occurrenceID,
                    format_gbif_date(observation.eventDateTime),
                    observation.scientificName,
                    observation.taxonRank,
                    observation.order,
                    observation.family,
                    observation.genus,
                    observation.specificEpithet,
                    observation.scientificNameAuthorship,
                    observation.lifeStage,
                    observation.sex,
                    observation.individualCount,
                    observation.decimalLatitude,
                    observation.decimalLongitude,
                    observation.coordinateUncertaintyInMeters,
                    observation.countryCode,
                    observation.county,
                    observation.municipality,
                    observation.locality,
                    observation.recordedBy,
                    recordedByID,
                    observation.identifiedBy,
                    identifiedByID,
                    observation.dateIdentified,
                    observation.occurrenceRemarks,
                    observation.imageFileNames]
                writer.writerow(row)

            temp_file.close()

            return send_file(
                temp_file.name,
                mimetype='text/csv',
                download_name='gbif_observation_export.csv',
                as_attachment=True
            )
        except Exception as e:
            temp_file.close()
            os.unlink(temp_file.name)
            raise e

    except Exception as e:
        return f"An error occurred: {str(e)}", 500