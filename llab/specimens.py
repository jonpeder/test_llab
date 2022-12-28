# load packages
from flask import Blueprint, redirect, url_for, escape, render_template, flash
from flask_login import login_required, current_user
import sqlite3
from .models import User, Collectors, Collecting_events, Country_codes, Collecting_methods, Print_events
from . import db
import subprocess

# connect to __init__ file
specimens = Blueprint('specimens', __name__)