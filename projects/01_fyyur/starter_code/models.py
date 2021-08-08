import psycopg2
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from forms import *
from app import * 



app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)



#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()), nullable=False)
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))

class Show(db.Model):
  __tablename__ = 'Show'

  show_id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)
  artist = db.relationship('Artist', backref=db.backref('shows', lazy=True, cascade='all, delete-orphan'))
  venue = db.relationship('Venue', backref=db.backref('shows', lazy=True, cascade='all, delete-orphan'))

  #artist = db.relationship('Artist', backref=db.backref('shows', lazy='joined', cascade='all, delete-orphan'))
  #venue = db.relationship('Venue', backref=db.backref('shows', lazy='joined', cascade='all, delete-orphan'))

  #Updated Show Many-to-Many relationship to include the relationship rows here instead of in the Artist and Venue tables.
  #Used following articles to learn and refactor the code:
  #https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html#many-to-many
  #https://docs.sqlalchemy.org/en/14/orm/backref.html#backref-arguments
  #https://docs.sqlalchemy.org/en/14/orm/cascades.html#backref-cascade
  #https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html