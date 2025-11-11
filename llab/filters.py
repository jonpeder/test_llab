from flask import Blueprint
from datetime import datetime
import re
from .models import Taxa
from . import db

# connect to __init__ file
filters = Blueprint('filters', __name__)

# Trim whitespaces
filters.trim_blocks = True
filters.lstrip_blocks = True

# Parse string to date format 
@filters.app_template_filter('string_to_date')
def string_to_date(date):
    date_format = datetime.strptime(str(date), "%Y-%m-%d")
    return date_format

# Parse string to date format 
@filters.app_template_filter('string_to_datetime')
def string_to_datetime(datetime):
    datetime_format = datetime.strptime(str(datetime), "%Y-%m-%d %H:%M:%S")
    return datetime_format

# scale numeric value by factor
@filters.app_template_filter('scale_value')
def scale_value(value, factor):
    return value*factor

# Format date
@filters.app_template_filter('date_format')
def date_format(date, format="%d.%m.%Y"):
    return date.strftime(format)


# Format datetime
@filters.app_template_filter('format_datetime')
def format_datetime(date_time):
    date = ""
    if date_time:
        date_time = datetime.strptime(str(date_time), "%Y-%m-%d %H:%M:%S")
        date = f'{date_time.strftime("%d")} {date_time.strftime("%b")} {date_time.strftime("%Y")}'
    return date


# Format dates
@filters.app_template_filter('format_dates')
def format_dates(date_1, date_2):
    # If date 1
    date = ""
    if date_1:
        date_1 = datetime.strptime(str(date_1), "%Y-%m-%d")
        date = f'{date_1.strftime("%d")} <b>{date_1.strftime("%b")}</b> {date_1.strftime("%Y")}'
        # If date 2
        if date_2:
            date_2 = datetime.strptime(str(date_2), "%Y-%m-%d")
            # If same year
            if date_1.strftime("%Y") == date_2.strftime("%Y"):
                # If same month
                if date_1.strftime("%m") == date_2.strftime("%m"):
                    date = f'{date_1.strftime("%d")}-{date_2.strftime("%d")} <b>{date_2.strftime("%b")}</b> {date_2.strftime("%Y")}'
                # If not same month
                else:
                    date = f'{date_1.strftime("%d")} <b>{date_1.strftime("%b")}</b>-{date_2.strftime("%d")} <b>{date_2.strftime("%b")}</b> {date_2.strftime("%Y")}'
            # If not same year
            else:
                date = f'{date_1.strftime("%d")} <b>{date_1.strftime("%b")}</b> {date_1.strftime("%Y")}-{date_2.strftime("%d")} <b>{date_2.strftime("%b")}</b> {date_2.strftime("%Y")}'
    # If only date 1
    return date

# Format dates 3
# Format dates for GBIF-export
@filters.app_template_filter('format_dates3')
def format_dates3(date_1, date_2):
    # If date 1
    if date_1:
        date_1 = datetime.strptime(str(date_1), "%Y-%m-%d")
        date = f'{date_1.strftime("%Y")}-{date_1.strftime("%m")}-{date_1.strftime("%d")}'
        # If date 2
        if date_2:
            date_2 = datetime.strptime(str(date_2), "%Y-%m-%d")
            # If same year
            if date_1.strftime("%Y") == date_2.strftime("%Y"):
                # If same month
                if date_1.strftime("%m") == date_2.strftime("%m"):
                    date = f'{date_2.strftime("%Y")}-{date_2.strftime("%m")}-{date_1.strftime("%d")}/{date_2.strftime("%d")}'
                # If not same month
                else:
                    date = f'{date_2.strftime("%Y")}-{date_1.strftime("%m")}-{date_1.strftime("%d")}/{date_2.strftime("%m")}-{date_2.strftime("%d")}'
            # If not same year
            else:
                date = f'{date_1.strftime("%Y")}-{date_1.strftime("%m")}-{date_1.strftime("%d")}/{date_2.strftime("%Y")}-{date_2.strftime("%m")}-{date_2.strftime("%d")}'
    # If only date 1
    return date

# Format dates. Months without <b> html tags
@filters.app_template_filter('format_dates2')
def format_dates2(date_1, date_2):
    # If date 1
    date = ""
    if date_1:
        date_1 = datetime.strptime(str(date_1), "%Y-%m-%d")
        date = f'{date_1.strftime("%d")} {date_1.strftime("%b")} {date_1.strftime("%Y")}'
        # If date 2
        if date_2:
            date_2 = datetime.strptime(str(date_2), "%Y-%m-%d")
            # If same year
            if date_1.strftime("%Y") == date_2.strftime("%Y"):
                # If same month
                if date_1.strftime("%m") == date_2.strftime("%m"):
                    date = f'{date_1.strftime("%d")}-{date_2.strftime("%d")} {date_2.strftime("%b")} {date_2.strftime("%Y")}'
                # If not same month
                else:
                    date = f'{date_1.strftime("%d")} {date_1.strftime("%b")}-{date_2.strftime("%d")} {date_2.strftime("%b")} {date_2.strftime("%Y")}'
            # If not same year
            else:
                date = f'{date_1.strftime("%d")} {date_1.strftime("%b")} {date_1.strftime("%Y")}-{date_2.strftime("%d")} {date_2.strftime("%b")} {date_2.strftime("%Y")}'
    # If only date 1
    return date

# Format Locality
@filters.app_template_filter('locality_format')
def locality_format(locality_1, locality_2):
    locality = ""
    if locality_2:
        locality = locality_2
    if locality_1:
        locality = locality_1
        if locality_2:
            locality = f'{locality_1}, {locality_2}'
    return locality

# Format recordedBy
@filters.app_template_filter('leg_format')
def leg_format(leg):
    # Split by separator
    leg = leg.split("|")
    # If more than one name
    if len(leg) > 1:
         # Strip leading ant tailing spaces
        leg = [i.strip() for i in leg]
        # Keep only surnames
        leg = [i.split(" ")[len(i.split(" "))-1] for i in leg]
        if len(leg) == 2:
            leg_out = ", ".join(leg[0:-1])+" & "+leg[-1]
        else:
            leg_out = f'{leg[0]} <i>et al.</i>'
    else:
        leg_out = leg[0]
    return leg_out

# Format scientific name. Used to format substrate names on the event-labels.
@filters.app_template_filter('scn_format')
def scn_format(name):
    name = name.strip() # Strip leading ant tailing spaces
    name = remove_author_string(name)
    if len(name.split(" ")) > 1:  # If binomial
        name = name.split(" ")
        name = name[0][0].upper()+". "+" ".join(name[1:])
    name = italicize_scientific_name(name)
    return name

# Returns scientific name without author string
@filters.app_template_filter('scn_italic_ex_author')
def scn_italic_ex_author(name, rank, author):
    # Remove autohor from name and remove trailing white-spaces
    if author:
        name = name.replace(author, "").strip()
    # If species or genus level use italic
    if rank=="species" or rank=="genus" or rank=="spnov":
        name=f'<i>{name}</i>'
    if rank == "species_group":
        name = f'<i>{name.replace("group", "").strip()}</i> group'
    return name

# More accurate than 'italicize_scientific_name' but requires rank and author string.
@filters.app_template_filter('scn_italic2')
def scn_italic2(name, rank, author):
    # Remove autohor from name and remove trailing white-spaces
    if author:
        name = name.replace(author, "").strip()
    # If species or genus level use italic
    if rank=="species" or rank=="genus" or rank=="spnov":
        name=f'<i>{name}</i>'
    if rank == "species_group":
        name = f'<i>{name.replace("group", "").strip()}</i> group'
    if author:
        name = f'{name} {author}'
    return name

# Redundant. Replace with italicize_scientific_name.
@filters.app_template_filter('scn_italic3')
def scn_italic3(name, rank):
    if rank=="genus":
        name_italic = name.split(" ")[0]
        name_author = " ".join(name.split(" ")[1:])
    else:
        if rank=="species_group":
            name = name.replace("group", "").strip()
        name_italic = " ".join(name.split(" ")[0:2])
        name_author = " ".join(name.split(" ")[2:])
    if name_author:
        if rank=="species_group":
            new_name = f'<i>{name_italic}</i> group {name_author}'
        else:
            new_name = f'<i>{name_italic}</i> {name_author}'
    else:
        if rank=="species_group":
            new_name = f'<i>{name_italic}</i> group'
        else:
            new_name = f'<i>{name_italic}</i>'
    return new_name

# Put scientific name within <i> tags
@filters.app_template_filter('italicize_scientific_name')
def italicize_scientific_name(name: str) -> str:
    if not name:
        return ""
    elif name.split(" ")[0][-4:] == "idae" or name.split(" ")[0][-4:] == "inae" or name.split(" ")[0][-3:] == "ini" or name.split(" ")[0][-6:] == "optera":
        return name
    else:
        # Regular expression to match binomial names or genus names
        pattern = re.compile(r"^(?P<name>[A-Z][a-z]+(?: [a-z]+)?) (?P<author>.*[A-Z].*)$")
        match = pattern.match(name)
        # If name looks like family or author
        if match:
            italicized_name = f"<i>{match.group('name')}</i> {match.group('author')}"
            return italicized_name
        else:
            return f"<i>{name}</i>"  # If no author string is found, italicize the whole input

# Remove author from scientific name
@filters.app_template_filter('remove_author_string')
def remove_author_string(name: str) -> str:
    # Regular expression to match binomial names or genus names
    if name:
        pattern = re.compile(r"^(?P<name>[A-Z][a-z]+(?: [a-z]+)?) (?P<author>.*[A-Z].*)$")
        match = pattern.match(name)
        if match:
            new_name = match.group('name')
            return new_name
        else:
            return name  # If no author string is found, italicize the whole input
    else:
        return ""

# Remove author from scientific name and use _ as separator
@filters.app_template_filter('remove_author_string2')
def remove_author_string(name: str) -> str:
    # Regular expression to match binomial names or genus names
    if name:
        pattern = re.compile(r"^(?P<name>[A-Z][a-z]+(?: [a-z]+)?) (?P<author>.*[A-Z].*)$")
        match = pattern.match(name)
        if match:
            name = match.group('name')
        name = name.replace(" ", "_")
        return name
    else:
        return ""


# if_present
@filters.app_template_filter('if_present')
def if_present(variable):
    if variable:
        variable_out = variable
    else:
        variable_out = ""
    return variable_out

# tablerow
@filters.app_template_filter('tablerow')
def if_present(value, header):
    if value:
        row = f'<tr><td>{header}</td><td>{value}</td></tr>'
    else:
        row = ""
    return row

# substrate
@filters.app_template_filter('format_substrate')
def format_substrate(substrateName, substratePlantPart, substrateType):
    if substrateName:
        substrateName = remove_author_string(substrateName)
        substrateName = italicize_scientific_name(substrateName)
        if substratePlantPart:
            if substrateType:
                substrate = f'{substrateName} {substratePlantPart}-{substrateType}'
            else:
                substrate = f'{substrateName} {substratePlantPart}'
        elif substrateType:
            substrate = f'{substrateName} {substrateType}'
        else:
            substrate = f'{substrateName}'
    else:
        substrate = ""
    return substrate

# Method abbreviation
@filters.app_template_filter('abbr')
def abbr(name):
    name = name.replace("-", " ")
    name = name.split(" ")
    name = "".join([i[0] for i in name])
    return name

# Debug
@filters.app_template_filter('debug')
def debug(text):
    print (text)
    return ''

# Wrap dna sequence
@filters.app_template_filter('wrap_dna_sequence')
def wrap_dna_sequence(sequence, n):
    return '<br>'.join(sequence[i:i+n] for i in range(0, len(sequence), n))

# Put eunis habitat code in parenthesis after habitat name
@filters.app_template_filter('format_eunis')
def format_eunis(habitat, code):
    if habitat:
        return f"{habitat} ({code})"
    else:
        return ""

