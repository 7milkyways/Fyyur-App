#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
  render_template, 
  request, 
  Response, 
  flash, 
  redirect, 
  url_for)
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from model import *
from config import DatabaseURI
import sys
from sqlalchemy import desc

moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = DatabaseURI.SQLALCHEMY_DATABASE_URI



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
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
  # geting latest artist and venues from db
  venues = Venue.query.order_by(desc(Venue.id)).limit(2).all()
  artists = Artist.query.order_by(desc(Artist.id)).limit(2).all()
  return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  data=[]

  regions = Venue.query.distinct(Venue.state, Venue.city).all()

  for region in regions:
    result = {
        'state': region.state,
        'city': region.city,
        'venues': []
      }
    venues = Venue.query.filter_by(state=region.state, city=region.city).all()

    get_venues = []
    for venue in venues:
      get_venues.append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': len(db.session.query(Show).join(Venue).all())
      })
    
    result['venues'] = get_venues
    data.append(result)


  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  search_term = request.form.get('search_term', '')

  venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
  
  response={
    "count": len(venues),
    "data": []
  }

 
  upcoming_shows = []

  for venue in venues:
    all_result = {
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(db.session.query(Show).join(Venue)
      .filter(Show.venue_id==venue.id)
      .filter(Show.start_time > datetime.now()).all()) # Get number of upcoming shows
    }

    all_result["num_upcoming_shows"] = upcoming_shows

    response["data"].append(all_result)
  
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue = Venue.query.filter_by(id=venue_id).first()
  all_genres = list(venue.genres.split(','))

  all_shows = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id)

  past_shows=[]
  upcoming_shows=[]

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": all_genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
  }

  
  for show in all_shows:
    if show.start_time < datetime.now():
      all_past_shows ={
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
      }
      past_shows.append(all_past_shows)
    elif show.start_time > datetime.now():
      all_upcomig_shows ={
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
      }
      upcoming_shows.append(all_upcomig_shows)


  data['past_shows'] = past_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows'] = upcoming_shows
  data['upcoming_shows_count'] = len(upcoming_shows)
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  form = VenueForm(request.form)

  if form.validate():
    try:
      venue = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        genres = ','.join(form.genres.data),
        website_link = form.website_link.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data
      )

      db.session.add(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except Exception:
      db.session.rollback()
      logging.info(sys.exc_info())
      flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    finally:
      db.session.close()
  else:
    logging.info(sys.exc_info())
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete', methods=['GET', 'DELETE'])
def delete_venue(venue_id):

  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully listed!')
  except Exception:
    db.session.rollback()
    logging.info(sys.exc_info())
    flash('An error occurred. Venue ' + venue.name + ' could not be listed.')
  finally:
    db.session.close()

  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()

  data = []
  for artist in artists:
    all_artists = {
      "id": artist.id,
      "name": artist.name
    }

    data.append(all_artists)


  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term = request.form.get('search_term', '')

  artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
  
  response={
    "count": len(artists),
    "data": []
  }

 
  all_result = {}
  upcoming_shows = []

  for artist in artists:
    all_result = {
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(db.session.query(Show).join(Venue)
      .filter(Show.artist_id==artist.id)
      .filter(Show.start_time > datetime.now()).all()) # Get number of upcoming shows
    }

    response["data"].append(all_result)
  

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist = Artist.query.filter_by(id=artist_id).first()
  all_genres = list(artist.genres.split(','))

  all_shows = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id)
 
  past_shows=[]
  upcoming_shows=[]

  data={
    "id": artist.id,
    "name": artist.name,
    "genres": all_genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
   
  }

  
  for show in all_shows:
    if show.start_time < datetime.now():
      all_past_shows ={
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
      }
      past_shows.append(all_past_shows)

    elif show.start_time > datetime.now():
      all_upcomig_shows ={
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
      }
      upcoming_shows.append(all_upcomig_shows)


  data['past_shows'] = past_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows'] = upcoming_shows
  data['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm(request.form)

  artist = Artist.query.get(artist_id)
  form.name.data = artist.name
  form.genres.data = artist.genres.split(',')
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website_link
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  form = ArtistForm(request.form)

  if form.validate():
    try:
      artist = Artist.query.filter_by(id=artist_id).first()
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.genres = ','.join(form.genres.data)
      artist.facebook_link = form.facebook_link.data
      artist.image_link = form.image_link.data
      artist.website_link = form.website_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description= form.seeking_description.data

      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + form.name.data + ' was successfully listed!')
    except Exception:
      db.session.rollback()
      logging.info(sys.exc_info())
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    finally:
      db.session.close()
  else:
    logging.info(sys.exc_info())
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm(request.form)

  venue = Venue.query.get(venue_id)

  form.name.data = venue.name
  form.genres.data = venue.genres.split(',')
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.website_link.data = venue.website_link
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)

  if form.validate():
    try:
      venue = Venue.query.filter_by(id=venue_id).first()
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.genres = ','.join(form.genres.data)
      venue.facebook_link = form.facebook_link.data
      venue.image_link = form.image_link.data
      venue.website_link = form.website_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description= form.seeking_description.data

      db.session.add(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + form.name.data + ' was successfully listed!')
    except Exception:
      db.session.rollback()
      logging.info(sys.exc_info())
      flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    finally:
      db.session.close()
  else:
    logging.info(sys.exc_info())
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')


  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  form = ArtistForm(request.form)

  if form.validate():
    try:
      artist = Artist(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        genres = ','.join(form.genres.data),
        facebook_link = form.facebook_link.data,
        image_link = form.image_link.data,
        website_link = form.website_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description= form.seeking_description.data,
      )

      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + form.name.data + ' was successfully listed!')
    except Exception:
      db.session.rollback()
      logging.info(sys.exc_info())
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    finally:
      db.session.close()
  else:
    logging.info(sys.exc_info())
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')


  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows = Show.query.all()
  data = []
  for show in shows:
    result = {
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S"),
    }
  
    data.append(result)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  form = ShowForm(request.form)

  if form.validate():
    try:
      show = Show(
      artist_id = form.artist_id.data,
      venue_id = form.venue_id.data,
      start_time = form.start_time.data
      )
      db.session.add(show)
      db.session.commit()
      # on successful db insert, flash success
      flash('Show was successfully listed!')
    except Exception:
      db.session.rollback()
      logging.info(sys.exc_info())
      flash('Show was not successfully listed!')
    finally:
      db.session.close()
  else:
    logging.info(sys.exc_info())
    flash('Show was not successfully listed!')

  return render_template('pages/home.html')

@app.errorhandler(400)
def bad_request_error(error):
  return render_template('errors/400.html'), 400

@app.errorhandler(401)
def unauthorized_error(error):
  return render_template('errors/401.html'), 401

@app.errorhandler(403)
def forbidden_error(error):
  return render_template('errors/403.html'), 403

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
