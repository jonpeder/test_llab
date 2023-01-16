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

# Debug
@filters.app_template_filter('debug')
def debug(text):
  print (text)
  return ''

