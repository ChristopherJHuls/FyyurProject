#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from datetime import date
import json
from operator import ge
import re
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form, CSRFProtect
from forms import *
from flask_migrate import Migrate
import psycopg2

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
#in config:
#SQLALCHEMY_DATABASE_URI = 'postgresql://postgres@localhost:5432/fyyur'

csrf.init_app(app)

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
  artist = db.relationship('Artist', backref=db.backref('shows', lazy='joined', cascade='all, delete-orphan'))
  venue = db.relationship('Venue', backref=db.backref('shows', lazy='joined', cascade='all, delete-orphan'))

  #Updated Show Many-to-Many relationship to include the relationship rows here instead of in the Artist and Venue tables.
  #Used following articles to learn and refactor the code:
  #https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html#many-to-many
  #https://docs.sqlalchemy.org/en/14/orm/backref.html#backref-arguments
  #https://docs.sqlalchemy.org/en/14/orm/cascades.html#backref-cascade
  #https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  value = value.strftime('%m/%d/%Y, %H:%M:%S')
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  venues = Venue.query.all()
  areas = Venue.query.distinct(Venue.city, Venue.state).all()

  for i in areas:
    data.append({
      'city': i.city,
      'state': i.state,
      'venues': [{
        'id': venue.id,
        'name': venue.name
      }
      for venue in venues if venue.city == i.city and venue.state == i.state]
      #Could not get this to organize by city. Modeled my solution above based on information found in this forum article:
      #https://knowledge.udacity.com/questions/501471
    })

  return render_template('pages/venues.html', areas = data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.items('search_term')
  name = ''
  for item in search_term:
    name = item[1]
    

  venues = Venue.query.filter(Venue.name.ilike('%' + name + '%')).all()

  response = {
    'count': len(venues),
    'data': []
  }

  for venue in venues:
    response['data'].append({
      'id': venue.id,
      'name': venue.name
    })

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  currentTime = datetime.now()

  upcoming_shows = Show.query.filter(Show.venue_id==venue_id, Show.start_time >= currentTime).all()
  past_shows = Show.query.filter(Show.venue_id==venue_id,Show.start_time < currentTime).all()
  #For filtering, I referenced the following forum article:
  #https://knowledge.udacity.com/questions/261355
  #I originally included the joins here but once I found the documentation for the lazy="joined" I was able to refine the query here just by going through Show

  data = {
    'id': venue.id,
    'name': venue.name,
    'city': venue.city,
    'state': venue.state,
    'address': venue.address,
    'phone': venue.phone,
    'image_link': venue.image_link,
    'facebook_link': venue.facebook_link,
    'genres': venue.genres,
    'website_link': venue.website_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'upcoming_shows': [{
      'artist_id': show.artist.id,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time
    } for show in upcoming_shows],
    'past_shows': [{
      'artist_id': show.artist.id,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time
    }for show in past_shows]
  }   
  return render_template('pages/show_venue.html', venue = data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form, meta={"csrf": False})
  if form.validate():
    try:
      data = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        genres = form.genres.data,
        website_link = form.website_link.data,
        seeking_talent = form.seeking_talent.data, 
        seeking_description = form.seeking_description.data 
      )
      db.session.add(data)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    finally:
      db.session.close()
    return render_template('pages/home.html')
  else:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    flash(f"{form.errors.items()}")
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete')
def delete_venue(venue_id):
  try: 
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.items('search_term')
  name = ''
  for item in search_term:
    name = item[1]

  artists = Artist.query.filter(Artist.name.ilike('%' + name + '%')).all()

  response = {
    'count': len(artists),
    'data': []
  }

  for artist in artists:
    response['data'].append({
      'id': artist.id,
      'name': artist.name
    })

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  currentTime = datetime.now()
  artist = Artist.query.get(artist_id)
  upcoming_shows = Show.query.filter(Show.artist_id==artist_id, Show.start_time >= currentTime).all()
  past_shows = Show.query.filter(Show.artist_id==artist_id , Show.start_time< currentTime).all()

  data = {
    'id': artist.id,
    'name': artist.name,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'genres': artist.genres,
    'facebook_link': artist.facebook_link,
    'image_link': artist.image_link,
    'website_link': artist.website_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description,
    'upcoming_shows': [{
      'venue_id': show.venue.id,
      'venue_image_link': show.venue.image_link,
      'start_time': show.start_time
    } for show in upcoming_shows],
    'past_shows': [{
      'venue_id': show.venue.id,
      'venue_image_link': show.venue.image_link,
      'start_time': show.start_time
    } for show in past_shows]
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form, meta={"csrf": False})
  if form.validate():
    try:
      artist = Artist.query.get(artist_id)
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.genres = form.genres.data
      artist.facebook_link = form.facebook_link.data
      artist.image_link = form.image_link.data
      artist.website_link = form.website_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_descripton = form.seeking_description.data
      db.session.add(artist)
      db.session.commit()
    except:
      db.session.rollback()
    finally:
      db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))
  else:
    flash(f"{form.errors.items()}")
    return redirect(url_for('show_artist', artist_id=artist_id))
    
  


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form, meta={"csrf": False})
  if form.validate():
    try: 
      venue = Venue.query.get(venue_id)
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.image_link = form.image_link.data
      venue.facebook_link = form.facebook_link.data
      venue.genres = form.genres.data
      venue.website_link = form.website_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data 
      db.session.add(venue)
      db.session.commit()
    except:
      db.session.rollback()
    finally:
      db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))
  else:
    flash(f"{form.errors.items()}")
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

  

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form, meta={"csrf": False})
  if form.validate():
    try:
      
      data = Artist(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        genres = form.genres.data,
        facebook_link = form.facebook_link.data,
        image_link = form.image_link.data,
        website_link = form.website_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data
      )
      db.session.add(data)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
      db.session.close()
    return render_template('pages/home.html')
  else: 
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    flash(f"{form.errors.items()}")
    return render_template('pages/home.html')



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  #TODO
  shows = Show.query.order_by(Show.start_time).all()

  for show in shows: 
    print(show)
  data = [{
    'venue_id': show.venue.id,
    'venue_name': show.venue.name,
    'artist_id': show.artist.id,
    'artist_name': show.artist.name,
    'artist_image_link': show.artist.image_link,
    'start_time': show.start_time
  } for show in shows]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form, meta={"csrf": False})
  if form.validate():
    try:
      data = Show(
        venue_id = form.venue_id.data,
        artist_id = form.artist_id.data,
        start_time = form.start_time.data
      )
      db.session.add(data)
      db.session.commit()
      flash('Show was successfully listed!')
    except:
      db.session.rollback()
      flash('An error occurred. Show could not be listed.')
    finally:
      db.session.close()
    return render_template('pages/home.html')
  else:
    flash(f"{form.errors.items()}")
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
