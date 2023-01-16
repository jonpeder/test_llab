from flask import Blueprint, current_app, flash, request, redirect, url_for, render_template, send_from_directory
from flask_login import login_required, current_user
from .models import User, Collecting_events, Occurrences, Occurrence_images, Taxa
from . import db
import os
import shutil
import glob
from werkzeug.utils import secure_filename

# connect to __init__ file
occurrences = Blueprint('occurrences', __name__)

# Specify app
app = current_app


# Function to add specimens to database and to update determinations

# Function 