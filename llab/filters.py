from flask import Blueprint
from datetime import datetime

# connect to __init__ file
filters = Blueprint('filters', __name__)

# Trim whitespaces
filters.trim_blocks = True
filters.lstrip_blocks = True

# custum filter
@filters.app_template_filter('add_dear')
def add_dear(name):
    return f'dear {name}'

# Parse string to date format 
@filters.app_template_filter('string_to_date')
def string_to_date(date):
    date_format = datetime.strptime(str(date), "%Y-%m-%d")
    return date_format

# Format date
@filters.app_template_filter('date_format')
def date_format(date, format="%d.%m.%Y"):
    return date.strftime(format)

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
        leg_out = ", ".join(leg[0:-1])+" & "+leg[-1]
    else:
        leg_out = leg[0]
    return leg_out

# Format scientificName
@filters.app_template_filter('scn_format')
def scn_format(name):
    name = name.strip() # Strip leading ant tailing spaces
    if len(name.split(" ")) == 2:  # If binomial
        name = name.split(" ")
        name = name[0][0].upper()+". "+name[1]
    return name

# Add italic-tags to scientificName. Use three arguments: scientificName, taxonRank and scientificNameAuthorship
@filters.app_template_filter('scn_italic')
def scn_italic(name, rank, author):
    # Remove autohor from name and remove trailing white-spaces
    name = name.replace(author, "").strip()
    # If species or genus level use italic
    if rank=="species" or rank=="genus" or rank=="spnov":
        name=f'<i>{name}</i>'
    if rank == "species_group":
        name = f'<i>{name.replace("group", "").strip()}</i> group'    
    return name

# Debug
@filters.app_template_filter('debug')
def debug(text):
  print (text)
  return ''

