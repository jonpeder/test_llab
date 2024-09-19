from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from os import getcwd
from flask_login import LoginManager
import pymysql

# Initiate web-app database
db = SQLAlchemy()
#DB_NAME = "insects.db"

# Upload folder path
home_dir = getcwd()
#home_dir = path.expanduser("~")
UPLOAD_FOLDER = path.join(home_dir, "llab/static/uploads")

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'fungusgnatsarecrazy'
    #app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:hane#1v1N@localhost/llab?charset=utf8mb4"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    db.init_app(app)

    from .auth import auth
    from .cevents import cevents
    from .researcher import researcher
    from .images import images
    from .taxa import taxa
    from .filters import filters
    from .specimens import specimens
    from .landmarks import landmarks
    from .datasets import datasets
    from .filter import filter
    from .collection import collection
    from .export import export
    from .observations import observations


    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(cevents, url_prefix='/')
    app.register_blueprint(researcher, url_prefix='/')
    app.register_blueprint(images, url_prefix='/')
    app.register_blueprint(taxa, url_prefix='/')
    app.register_blueprint(filters, url_prefix='/')
    app.register_blueprint(specimens, url_prefix='/')
    app.register_blueprint(landmarks, url_prefix='/')
    app.register_blueprint(datasets, url_prefix='/')
    app.register_blueprint(filter, url_prefix='/')
    app.register_blueprint(collection, url_prefix='/')
    app.register_blueprint(export, url_prefix='/')
    app.register_blueprint(observations, url_prefix='/')


    from .models import User, Catalog_number_counter, Print_events, Print_det, Event_images, Occurrence_images, Identification_events, Eunis_habitats, Observations

    with app.app_context():
        db.create_all()

    #db.create_all(app=app)

    login_manager = LoginManager()
    # Redirect to login-page if not logged in
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)  # Tell login manager which app we are using

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

app = create_app()
