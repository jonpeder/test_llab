from .models import Catalog_number_counter, Unit_id_counter, Pteromalidae_norway
from . import db
from sqlalchemy import func
# Read strandr.tmp csv file to python dictionary
import csv
# Importing libraries for QrReader
import re
import cv2
import numpy as np
import pandas as pd
import datetime as dt
from datetime import datetime
#from pyzbar.pyzbar import decode
#from pyzbar.pyzbar import ZBarSymbol
from collections import defaultdict, Counter
from .filters import leg_format, format_dates2, italicize_scientific_name

def newEventID(eventID_list, prefix):
    # Get all IDs that start with the prefix and don't start with prefix_A
    matching_ids = [
        i for i in eventID_list 
        if i.startswith(prefix) and not i.startswith(f'{prefix}_A')
    ]
    
    if not matching_ids:
        return f'{prefix}0001'
    
    # Extract numeric parts
    numbers = []
    for id_str in matching_ids:
        # Get the part after prefix
        num_part = id_str[len(prefix):]
        try:
            numbers.append(int(num_part))
        except ValueError:
            continue
    
    if not numbers:
        return f'{prefix}0001'
    
    max_num = max(numbers)
    return f'{prefix}{max_num + 1:04d}'

# Add record to catalg_number_counter
def new_catalog_number ():
    new_number = Catalog_number_counter()
    db.session.add(new_number)
    db.session.commit()
    db.session.refresh(new_number)
    catalog_number = "{:0>6}".format(new_number.id)
    return(catalog_number)

def new_unit_id ():
    new_number = Unit_id_counter()
    db.session.add(new_number)
    db.session.commit()
    db.session.refresh(new_number)
    return(new_number.id)

# Arrange data from db-query in dict for presentation in bar-plot
def bar_plot_dict(dataframe, gr, percentage):
    # Group occurrences by predefined group
    if gr == "year" or gr == "month" or gr == "yearmonth":
        dataframe["date"] = dataframe["date"].astype("datetime64[ns]")
        if gr == "month":
            gr = "date"
            group = dataframe[gr].groupby(dataframe["date"].dt.month).count()
        if gr == "year":
            gr = "date"
            group = dataframe[gr].groupby(dataframe["date"].dt.year).count()
        if gr == "yearmonth":
            gr = "date"
            group = dataframe[gr].groupby([dataframe["date"].dt.year, dataframe["date"].dt.month]).count()
    else:
        group = dataframe[gr].groupby(dataframe[gr]).count()
    # Create dataframe
    groups_df = pd.DataFrame({"count":list(group)}, index=list(group.index))
    groups_df = groups_df.sort_values(by=['count'])
    # Add percentages to new column
    groups_df['perc'] = groups_df['count']/groups_df['count'].sum()*100
    # Concatenate columns containing less than 5% of occurrences into new column called 'other'
    # Set percentage limit
    p = percentage
    # New column values
    other_sum = groups_df['count'][groups_df['perc']<p].sum()
    other_perc = groups_df['perc'][groups_df['perc']<p].sum()
    # Remove columns containing less than 5% of occurrences
    groups_df = groups_df[groups_df['perc']>p]
    groups_df.loc['Other groups'] = [other_sum, other_perc]
    # Sort rows by count
    groups_df = groups_df.sort_values(by=['count'])
    # Drop rows with empty index name
    if '' in groups_df.index:
        groups_df = groups_df.drop([''])
    # Drop other groups if count = 0
    if groups_df.loc["Other groups"]["count"] == 0:
        groups_df = groups_df.drop(["Other groups"])
    # Transform back to dict
    dict_out = {"label":list(groups_df.index), "count":list(groups_df["count"])}
    return(dict_out)

# Read CSV
def readcsv(file):
    reader = csv.DictReader(open(file, newline=''),
                            delimiter=' ', quotechar='"')
    dictobj = next(reader)
    return (dictobj)

# Define query function
def query(conn, sql):
    c = conn.cursor()
    c.execute(sql)
    return c.fetchall()

# Define query function
def headers(conn, sql):
    # Create a cursor
    c = conn.cursor()
    # Execute query
    c.execute(sql)
    # Return headers
    return list(map(lambda x: x[0], c.description))
        
# Function: suggest new drawerID
def newDrawerName(existing_names_list, new_drawer_name):
    while True:
        try:
            maching_existing_names = [i for i in existing_names_list if new_drawer_name.split("_")[0] == i.split("_")[0]]
            if len(maching_existing_names) == 0:
                return f'{new_drawer_name}'
            elif len(maching_existing_names) == 1:
                if "_" in new_drawer_name:
                    return f'{new_drawer_name.split("_")[0]}_{int(new_drawer_name.split("_")[1])+1}'
                elif f'{new_drawer_name}' == maching_existing_names[0]:
                    return f'{new_drawer_name}_1'
                else:
                    return f'{new_drawer_name}'
            else:
                integer_list = []
                for i in maching_existing_names:
                    if "_" in i:
                        integer_list.append(int(i.split("_")[1]))
                integer_list.sort(reverse=True)
                return f'{new_drawer_name.split("_")[0]}_{integer_list[0]+1}'
        except:
            return f'{new_drawer_name}'     


# Function to decode qrcodes
def BarcodeReader(image):

    # read the image in numpy array using cv2
    #img = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
    img = image
    
    # Create two differently processed images
    test1 = img
    test2 = img
    # Image process 1 
    # Blur
    test1 = cv2.GaussianBlur(test1, (5, 5), 0.8)
    # Contrast
    alpha = 1.5 # Contrast control (1.0-3.0)
    beta = 0 # Brightness control (0-100)
    test1 = cv2.convertScaleAbs(test1, alpha=alpha, beta=beta)

    # Image process 2
    # Scale down
    scale = 0.4
    width = int(test1.shape[1] * scale)
    height = int(test1.shape[0] * scale)
    test2 = cv2.resize(test2, (width, height))
    # Binerize
    test2 = cv2.adaptiveThreshold(test2,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
    
    # Decode the barcode image
    # Decode test1
    decoded1 = decode(test1, symbols = [ZBarSymbol.QRCODE])
    test1_data = []
    for i in decoded1:
        test1_data.append(i.data)
    
    # Decode test2
    decoded2 = decode(test2, symbols = [ZBarSymbol.QRCODE])
    test2_data = []
    for i in decoded2:
        test2_data.append(i.data)
    
    

    # If not detected then print the message
    if not set(test1_data).union(test2_data):
        #print("Barcode Not Detected!")
        return ""
    else:
        # Print the barcode data
        #print(set(test1_data).union(test2_data))
        
        # Convert image from grayscale to color
        img=cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        # Polygon variables
        isClosed = True # Closed polygon
        color = (0, 0, 288) # Red color in BGR
        thickness = 10  # Line thickness of 2 px

        # Add detected barcodes
        for barcode in decoded1:  
            # Locate the barcode position in image
            (a, b, c, d) = barcode.polygon
            pts = np.array([[a.x, a.y], [b.x, b.y], [c.x, c.y], [d.x, d.y]],np.int32)
            img = cv2.polylines(img, [pts], isClosed, color, thickness)


        # Add barcodes detected from the down-scaled image
        scale=2.5
        for barcode in decoded2:  
            # Locate the barcode position in image
            (a, b, c, d) = barcode.polygon
            pts = np.array([[a.x*scale, a.y*scale], [b.x*scale, b.y*scale], [c.x*scale, c.y*scale], [d.x*scale, d.y*scale]], np.int32)
            img = cv2.polylines(img, [pts], isClosed, color, thickness)
        
        # Return combined barcode-data-sets and image with decoded barcodes
        return set(test1_data).union(test2_data), img

# Compress image function
def compress_image(input_image_path, output_image_path, quality):
    """
    Compresses an image and saves it to the specified output path.

    Parameters:
    input_image_path (str): Path to the input image.
    output_image_path (str): Path to save the compressed image.
    quality (int): Quality of the compressed image (0 to 100).
    """
    img = cv2.imread(input_image_path)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    cv2.imwrite(output_image_path, img, encode_param)



# country
# recordedBy
# coordinates
# institutionCode
# occurrenceID
# catalogNumber
# include_method
def format_occurrence_block(occurrence_ids, occurrences_dict, include_country = True, include_recordedBy = True, include_institutionCode = True, include_occurrenceID = True, include_catalogNumber = True, include_method = True):
    """
    Group occurrences by:
      country → stateProvince → county → strand_id → municipality → locality_1 → locality_2 → habitat → method → (d1, d2)
    Then format them in a compact faunistic report, reducing repetition.

    The final output has the format (per 'block'):

    Material: <country>, <stateProvince>, <county>, <strand_id>, <municipality>: <loc1>, <loc2> (<habitat>). <method>: <date>, <recordedBy>, <ownerInstitutionCode> <count>+<sex> [<specimenIDs>]

    Multiple blocks are separated by semicolons (“; ”).
    """

    # 1. Gather all relevant occurrences
    records = [occurrences_dict[oid] for oid in occurrence_ids if oid in occurrences_dict]
    if not records:
        return ""  # no data

    # 2. Build a nested dictionary for each hierarchy level.
    #    groups[country][stateProvince][county][strand_id][municipality][loc1][loc2][habitat][method][(d1, d2)] = list_of_records
    groups = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: defaultdict(
                        lambda: defaultdict(
                            lambda: defaultdict(
                                lambda: defaultdict(
                                    lambda: defaultdict(
                                        lambda: defaultdict(list)
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )

    for r in records:
        country       = (r.get("country") or "").upper()
        stateProvince = (r.get("stateProvince") or "").upper()
        county        = (r.get("county") or "").upper()
        strand_id     = (r.get("strand_id") or "").upper()
        municipality  = r.get("municipality") or ""
        loc1          = r.get("locality_1") or ""
        loc2          = r.get("locality_2") or ""
        habitat       = r.get("habitat") or ""
        method        = r.get("samplingProtocol") or ""
        d1            = r.get("eventDate_1") or ""
        d2            = r.get("eventDate_2") or ""

        groups[country][stateProvince][county][strand_id][municipality][loc1][loc2][habitat][method][(d1, d2)].append(r)

    # 3. Build the final string
    #    We'll create a block for each nested path. 
    #    For each (d1, d2), we aggregate sexes, gather IDs, and assume they share the same collector, institution, etc.
    #    Important! We assume each group of occurrences (sharing the same date range) has the same collector (recordedBy) and owner (ownerInstitutionCode). If not, you might need to further subdivide those records or handle them differently.

    top_level_blocks = []

    for country in sorted(groups.keys()):
        country_blocks = []
        for stateProvince in sorted(groups[country].keys()):
            state_blocks = []
            for county in sorted(groups[country][stateProvince].keys()):
                county_blocks = []
                for strand_id in sorted(groups[country][stateProvince][county].keys()):
                    strand_blocks = []
                    for municipality in sorted(groups[country][stateProvince][county][strand_id].keys()):
                        municipality_blocks = []
                        for loc1 in sorted(groups[country][stateProvince][county][strand_id][municipality].keys()):
                            loc1_blocks = []
                            for loc2 in sorted(groups[country][stateProvince][county][strand_id][municipality][loc1].keys()):
                                loc2_blocks = []
                                for habitat in sorted(groups[country][stateProvince][county][strand_id][municipality][loc1][loc2].keys()):
                                    habitat_blocks = []
                                    for method in sorted(groups[country][stateProvince][county][strand_id][municipality][loc1][loc2][habitat].keys()):
                                        date_blocks = []
                                        for (d1, d2) in sorted(groups[country][stateProvince][county][strand_id][municipality][loc1][loc2][habitat][method].keys(), key=lambda x: x[0]):
                                            recs = groups[country][stateProvince][county][strand_id][municipality][loc1][loc2][habitat][method][(d1, d2)]
                                            # Summarize sexes
                                            sex_counter = Counter(r["sex"] for r in recs)
                                            # Build a string, e.g. "1♀1♂"
                                            sex_parts = []
                                            for sex_key, count in sex_counter.items():
                                                if sex_key == "female":
                                                    if count > 1:
                                                        sex_parts.append(f"{count}♀︎♀︎")
                                                    else:
                                                        sex_parts.append(f"♀︎")
                                                elif sex_key == "male":
                                                    if count > 1:
                                                        sex_parts.append(f"{count}♂︎♂︎")
                                                    else:
                                                        sex_parts.append(f"♂︎")
                                                else:
                                                    # Possibly handle unknown sexes or other categories
                                                    if count > 1:
                                                        sex_parts.append(f"{count} Specim.")
                                                    else:
                                                        sex_parts.append("")

                                            # Join them with no space or with a plus, as desired
                                            # Example: "1♀︎1♂︎" or "3♀︎+2♂︎"
                                            # For the example, let's just put them directly with no separator or with a plus in between:
                                            # e.g. "3♀︎3♂︎"
                                            sex_str = "".join(sex_parts)
                                            if sex_str:
                                                sex_str = " " + sex_str

                                            # Gather occurrence IDs
                                            if include_catalogNumber:
                                                all_ids = [r["catalogNumber"] for r in recs]
                                            if include_occurrenceID:
                                                all_ids = [r["occurrenceID"] for r in recs]
                                            if include_catalogNumber or include_occurrenceID:
                                                id_str = ", ".join(all_ids)
                                            else: 
                                                id_str = ""
                                            if id_str:
                                                id_str = f" [{id_str}]"

                                            # Assume collector, owner are the same for all
                                            if include_recordedBy:
                                                recordedBy = recs[0].get("recordedBy") or ""
                                            else:
                                                recordedBy = ""
                                            if include_institutionCode:
                                                owner = recs[0].get("ownerInstitutionCode") or ""
                                            else:
                                                owner = ""

                                            date_str = format_dates2(d1, d2)

                                            # Example final piece for each date-block:
                                            #   "<method>: <date_str>, Leg. <recordedBy>, <owner> <sex_str> [<id_str>]"
                                            inner_block = []
                                            if date_str:
                                                inner_block.append(date_str)
                                            if method and include_method:
                                                inner_block.append(method)
                                            if recordedBy:
                                                inner_block.append(f"Leg. {leg_format(recordedBy)}")
                                            inner_block.append(f"{owner}{sex_str}{id_str}")
                                            inner_block_str = ", ".join(inner_block)

                                            #line_str = ", ".join([date_str, method, f"Leg. {leg_format(recordedBy)}", f"{owner}{sex_str}{id_str}"])
                                            #line = (
                                            #    f"{method}: {date_str}, Leg. {leg_format(recordedBy)}, {owner}{sex_str}{id_str}"
                                            #)
                                            date_blocks.append(inner_block_str)

                                        # Combine date blocks with semicolons
                                        habitat_block = "; ".join(date_blocks)
                                        # Add habitat info as: "(habitat)"
                                        if habitat:
                                            # E.g., "<loc2> (<habitat>). <method>..."
                                            # We'll build the chain after the loop to place them in the final location string
                                            habitat_blocks.append(habitat_block)
                                        else:
                                            habitat_blocks.append(habitat_block)

                                    # Combine method blocks for each habitat
                                    combined_habitat_block = "; ".join(habitat_blocks)
                                    if habitat:
                                        # We'll handle the parentheses around habitat when building the loc2-block 
                                        loc2_blocks.append(combined_habitat_block)
                                    else:
                                        loc2_blocks.append(combined_habitat_block)

                                # loc2-level combination
                                final_loc2_str = "; ".join(loc2_blocks)
                                if loc1 or loc2 or habitat:
                                    # e.g. "loc1, loc2 (habitat). <methods-block>... 
                                    block_str = ""
                                    if loc1:
                                        block_str += loc1
                                        if loc2:
                                            block_str += f", {loc2}"
                                    if habitat:
                                        block_str += f" ({habitat})"
                                    if block_str:
                                        block_str += ", "
                                    # Then append the rest (which is date_blocks, method, etc.)
                                    block_str += final_loc2_str
                                    loc1_blocks.append(block_str)
                                else:
                                    loc1_blocks.append(final_loc2_str)

                            # loc1-level combination
                            final_loc1_str = "; ".join(loc1_blocks)
                            if loc1:
                                loc1_block = final_loc1_str
                                municipality_blocks.append(loc1_block)
                            else:
                                municipality_blocks.append(final_loc1_str)

                        # municipality-level combination
                        final_muni_str = "; ".join(municipality_blocks)
                        if municipality:
                            muni_block = f"{municipality}: {final_muni_str}"
                            strand_blocks.append(muni_block)
                        else:
                            strand_blocks.append(final_muni_str)

                    # strand-level combination
                    final_strand_str = "; ".join(strand_blocks)
                    if strand_id:
                        strand_block = f"<b>{strand_id}</b>, {final_strand_str}"
                        county_blocks.append(strand_block)
                    else:
                        county_blocks.append(final_strand_str)

                # county-level combination
                final_county_str = "; ".join(county_blocks)
                if county:
                    county_block = f"{county}, {final_county_str}"
                    state_blocks.append(county_block)
                else:
                    state_blocks.append(final_county_str)

            # stateProvince-level combination
            final_state_str = "; ".join(state_blocks)
            if stateProvince:
                state_block = f"{stateProvince}, {final_state_str}"
                country_blocks.append(state_block)
            else:
                country_blocks.append(final_state_str)

        # country-level combination
        final_country_str = "; ".join(country_blocks)
        if country and include_country:
            country_block = f"<b>{country}</b>, {final_country_str}"
            top_level_blocks.append(country_block)
        else:
            top_level_blocks.append(final_country_str)

    # 4. Combine all top-level blocks 
    final_str = "; ".join(top_level_blocks)
    # Prepend "Material:"
    final_str = f"<b>Material:</b> {final_str}."
    return final_str

def format_associates_block(occurrence_ids, occurrences_dict):
    # Create a list of unique associated taxa
    associates = []
    for occurrence in occurrence_ids:
        if occurrences_dict[occurrence]["associatedTaxa"]:
            if occurrences_dict[occurrence]["associatedTaxa"] not in associates:
                associates.append(occurrences_dict[occurrence]["associatedTaxa"])
    
    # Put scientific name in italic
    associates = [italicize_scientific_name(name) for name in associates]
    # Join list
    if len(associates) > 2:
        associates_block = ", ".join(associates[:-1]) + " and " + associates[-1]
    else:
        associates_block = " and ".join(associates)
    if associates_block:
        return f", associated with {associates_block}."
    else:
        return ""
            

def format_biology_block(occurrence_ids, occurrences_dict):
    """
    Build a 'Biology' paragraph from the following hierarchy:
        method → (substratePlantPart + substrateType) → substrateName

    The final output has the format:
    Biology: <Verb> <preposition> <substratePlantPart>-<substrateType> of <substrateName>;
             <substrateName>; ...
             <Verb> <preposition> <substratePlantPart>-<substrateType> of <substrateName>; ...
             <etc.>

    where 'Verb' and 'preposition' depend on the method:
        - method == 'rared'       → "Rared" and "from"
        - method == 'hand-picked' → "Collected" and "on"
        - method == 'sweep-net'   → "Sweeped" and "from"
    """

    # 1. Define how each method maps to Verb & Preposition
    method_map = {
        "rared":       {"verb": "rared",     "prep": "from"},
        "hand-picked": {"verb": "collected", "prep": "on"},
        "sweep-net":   {"verb": "sweeped",   "prep": "from"},
    }

    # 1. Gather all relevant occurrences
    records = [occurrences_dict[oid] for oid in occurrence_ids if oid in occurrences_dict]
    if not records:
        return ""  # no data

    # 2. Build a nested dict:
    #    biology_dict[method][ (substratePlantPart, substrateType) ] = set_of_substrateNames
    biology_dict = defaultdict(lambda: defaultdict(set))

    for r in records:
        method              = r.get("samplingProtocol", "").lower()  # e.g. "rared", "hand-picked", "sweep-net"
        substratePlantPart  = r.get("substratePlantPart")  or ""
        substrateType       = r.get("substrateType")       or ""
        substrateName       = r.get("substrateName")       or ""

        # Only group if there's a method and a substrateName (otherwise skip)
        if method and substrateName:
            key = (substratePlantPart, substrateType)
            biology_dict[method][key].add(substrateName)

    
    # 3. Build the text, method by method
    #    Example: "Rared from leaf-gall of Centaurea jacea; Centaurea scabiosa; ...
    #              Collected on leaf-gall of Tragopogon pratense; ... etc."
    method_chunks = []
    for method_key, parttype_dict in biology_dict.items():
        # Map the method to the correct verb and preposition (default if missing)
        method_info = method_map.get(method_key, {"verb": method_key.title(), "prep": "from"})
        verb = method_info["verb"]
        prep = method_info["prep"]

        # Collect chunks of the form "<verb> <prep> <part>-<type> of <names>"
        # but we want to merge multiple (substratePlantPart, substrateType).
        # We'll produce something like:
        # "Rared from leaf-gall of Centaurea jacea; Centaurea scabiosa; ...
        #  flower-gall of Centaurea scabiosa; leaf-mine of Cirsium hetrophyllum"
        # Then separate them with semicolons.

        sub_chunks = []
        for (plant_part, sub_type), name_set in parttype_dict.items():
            # e.g. "leaf-gall", "flower-gall", "leaf-mine" etc.
            # If both are present: "leaf-gall" => f"{plant_part}-{sub_type}"
            # If one is empty, just skip the dash. 
            if plant_part and sub_type:
                part_type_str = f"{plant_part}-{sub_type}"
            else:
                part_type_str = (plant_part or sub_type)

            # Join all substrateNames with "; "
            # e.g. "of Centaurea jacea; Centaurea scabiosa; Cirsium hetrophyllum"
            name_list = sorted(name for name in name_set if name)  # omit empty
            # Put each name in italic and if name consist of one word (genus), add suffix " sp."
            name_list = [italicize_scientific_name(name) for name in name_list]
            if name_list:
                # "part-type of name1; name2; name3"
                name_str = "; ".join(name_list)
                chunk = f"{part_type_str} of {name_str}"
            else:
                # If no substrateName, skip the "of X" portion
                chunk = part_type_str

            # e.g. "leaf-gall of Centaurea jacea; Cirsium hetrophyllum"
            sub_chunks.append(chunk)

        # Combine all sub_chunks for this method
        # e.g. "leaf-gall of Centaurea jacea; Cirsium hetrophyllum; flower-gall of Centaurea scabiosa"
        if sub_chunks:
            sub_str = "; ".join(sub_chunks)
            # Full method portion: "<Verb> <prep> <sub_str>"
            method_chunk = f"{verb} {prep} {sub_str}"
            method_chunks.append(method_chunk)

    # 4. Combine method_chunks into a single paragraph
    #    e.g. "Rared from leaf-gall of Centaurea jacea; ...; Collected on leaf-gall of Tragopogon pratense; ..."
    if method_chunks:
        biology_paragraph = "; ".join(method_chunks)
        # First letter in lowercase
        biology_paragraph = biology_paragraph[:1].lower() + biology_paragraph[1:]
        return f"<p><b>Biology:</b> Material {biology_paragraph}{format_associates_block(occurrence_ids, occurrences_dict)}</p>"
    else:
        # If there's no biology info, return an empty string (or your preferred fallback)
        return ""
    
def extract_year(reference):
    """Helper function to extract the year from a reference string."""
    match = re.search(r"\b\d{4}\b", reference)  # Find a 4-digit year
    if match:
        return int(match.group())  # Convert the year to an integer for sorting
    return 0  # Default value if no year is found

def format_distribution_block(scientificName, output = "full", output_type = "strand"):
    # Make database query for strand-codes and references of the given species
    result = Pteromalidae_norway.query.filter_by(scientificName=scientificName).with_entities(Pteromalidae_norway.strand, Pteromalidae_norway.reference, Pteromalidae_norway.source).all()
    
    if result:
        # Create lists of unique strand-codes and references
        strand_list = []
        reference_list = []
        for row in result:
            if row.strand and row.strand not in strand_list:
                strand_list.append(row.strand)
            if row.reference and row.reference not in reference_list:
                reference_list.append(row.reference)
            if row.source == "GBIF" and "GBIF 2024" not in reference_list:
                reference_list.append("GBIF 2024")
            if row.source == "ADB" and "Artsdatabanken 2024" not in reference_list:
                reference_list.append("Artsdatabanken 2024")
        
        # Sort references by year and strand-codes alphanumerically
        reference_list.sort(key=extract_year)
        strand_list.sort()

        # Remove "UNKNOWN"
        if "UNKNOWN" in strand_list:
            if len(strand_list) > 1:
                strand_list.remove("UNKNOWN")
            else:
                strand_list = ['<span style="color: red">MISSING DATA</span>']

        # Join strand lists
        if len(strand_list) > 2:
            strand_chunk = ", ".join(strand_list[:-1]) + " and " + strand_list[-1]
        else:
            strand_chunk = " and ".join(strand_list)
        
        # Join reference list
        reference_chunk = ", ".join(reference_list)
        
        # Return a distribution description
        if output == "table":
            if output_type == "strand":
                return ", ".join(strand_list)
            else:
                return reference_chunk
        else:
            return f'<p><b>Distribution:</b> In Norway previously known from {strand_chunk} ({reference_chunk}).</p>'
    else:
        return ""
    
def format_new_distribution(scientificName, occurrences_dict, occurrence_ids):
    # Make database query for strand-codes of the given species
    stand_query = Pteromalidae_norway.query.filter_by(scientificName=scientificName).with_entities(Pteromalidae_norway.strand).all()
    # Create lists of unique strand-codes and references
    strand_new = []
    if stand_query:
        strand_old = []
        for row in stand_query:
            if row.strand and row.strand not in strand_old:
                strand_old.append(row.strand)
        for occurrence in occurrence_ids:
            if strand_old:
                print(strand_old)
                if occurrences_dict[occurrence]["strand_id"] not in strand_old:
                    if occurrences_dict[occurrence]["strand_id"] not in strand_new:
                        strand_new.append(occurrences_dict[occurrence]["strand_id"])
        if strand_new:
            strand_new.sort()
            return ", ".join(strand_new)
        else:
            return ""
    else:
        for occurrence in occurrence_ids:
            if occurrences_dict[occurrence]["strand_id"] not in strand_new:
                strand_new.append(occurrences_dict[occurrence]["strand_id"])
        if strand_new:
            strand_new.sort()
            return ", ".join(strand_new)
        else:
            return ""
    

def number_of_individuals(occurrence_ids, occurrences_dict):
    sexes = []
    individuals = 0
    for occurrence in occurrence_ids:
        sexes.append(occurrences_dict[occurrence]["sex"])
        individuals += occurrences_dict[occurrence]["individualCount"]
    males = sexes.count("male")
    females = sexes.count("female")
    individuals_string = []
    if not females and not males:
        individuals_string.append(f'{individuals}')
    if females:
        individuals_string.append(f'{females}♀︎')
    if males:
        individuals_string.append(f'{males}♂︎')
    return " ".join(individuals_string)

def format_gbif_date(eventDateTime):
    """Format date for GBIF compatibility"""
    if not eventDateTime:
        return ""
    
    if isinstance(eventDateTime, datetime):
        return eventDateTime.isoformat()
    
    try:
        # Parse and reformat if it's a string
        return datetime.fromisoformat(str(eventDateTime)).isoformat()
    except:
        return str(eventDateTime)