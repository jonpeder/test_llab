from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

# Initiate web-app database
db = SQLAlchemy()
DB_NAME = "insects.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'pteromalidsarebeautiful'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    from .views import views
    from .auth import auth
    from .cevents import cevents
        
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(cevents, url_prefix='/')
    
    
    from .models import User, Note, Print_events
    
    db.create_all(app=app)
    
    login_manager = LoginManager() 
    login_manager.login_view = 'auth.login' # Redirect to login-page if not logged in 
    login_manager.init_app(app) # Tell login manager which app we are using
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app

app = create_app()
