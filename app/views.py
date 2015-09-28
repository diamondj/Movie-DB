from flask import render_template, flash, redirect, session, url_for, request, jsonify, g, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask_bootstrap import Bootstrap
from datetime import datetime
from app import app, db, models, lm
from .models import Movie, Rating, Category, Links, User
from sqlalchemy import desc, func, and_, or_
from sqlalchemy.orm import load_only
from forms import RegistrationForm, LoginForm
import string
import recommend_user as rec
import numpy as np
import random


# helper function
def preprocess(s):
    return unicode(s, errors='ignore').strip()


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user


# API endpoint
# Return JSON 
@app.route('/movie/api/json/<movie_id>', methods=['GET'])
def movieJSON(movie_id):
    movie = db.session.query(Movie.id, 
    						 Movie.title, 
    						 Movie.year, 
    						 func.avg(Rating.score).label('ratings'), 
    						 func.count(Rating.score).label('reviews')).\
    						 filter(Movie.id == movie_id).\
    						 join(Rating, Rating.movie_id == Movie.id).first()
    if movie == []:
    	return str([])
    links = db.session.query(Links).filter(Links.movie_id == movie_id).first()
    styles = db.session.query(Category.category).filter(Category.movie_id == movie_id).all()
    return jsonify(movie = movie, links = links.serialize, styles= styles)

# API endpoint
# Return movie in certain genre in JSON
@app.route('/movie/api/json/genre/<genre>', methods=['GET'])
def genreJSON(genre):
	genre = genre.capitalize()
	q1 = db.session.query(Movie.id, Movie.title, Movie.year).\
		 join(Category, Category.movie_id == Movie.id).\
		 filter(Category.category == genre).subquery()
	movies = db.session.query(q1.c.id.label('id'), 
							  q1.c.title.label('title'), 
							  q1.c.year.label('year'), 
							  func.avg(Rating.score).label('ratings'), 
							  func.count(Rating.score).label('reviews')).\
							  join(Rating, Rating.movie_id == q1.c.id).\
							  group_by(Rating.movie_id).all()
	return jsonify(movies = movies)

# API intro and search page
@app.route('/movie/api', methods=['GET', 'POST'])
@login_required
def api():
	if request.method == "POST":
		if request.form['Check'] == 'Check by id':
			id = request.form['id']
			redirect(url_for('movieJSON', movie_id = id))
		if request.form['Check'] == 'Check by name':
			name = request.form['name']
			movie = db.session.query(Movie).filter_by(title = name).first()
			if movie == None:
				flash('No movie found')
			else:
				redirect(url_for('movieJSON', movie_id = movie.id))
	return render_template('api.html', user = g.user)

# register
@app.route('/register' , methods=['GET','POST'])
def register():
	form = RegistrationForm(request.form)
	if request.method == 'POST' and form.validate():
		preusers = db.session.query(User.username).filter_by(username = form.username.data).all()
		if len(preusers) > 0:
			flash('Name already registered!')
			return render_template('register.html', form=form)
		user = models.User(username = form.username.data, email = form.email.data, password = form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('Thanks for registering')
		return redirect(url_for('index'))
	return render_template('register.html', form=form, user = g.user)

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
	if g.user is not None and g.user.is_authenticated():
		return redirect(url_for('index'))
	form = LoginForm(request.form)
	if request.method == 'POST' and form.validate():
		username = form.username.data
		password = form.password.data
		user = db.session.query(User).filter_by(username = username).filter_by(password = password).first()
		if user != None:
			flash('Logged in successfully.')
			next = request.args.get('next')
			if next:
				return abort(400)
			login_user(user, remember = True)
			return redirect(url_for('index'))
		else:
			flash("Wrong username or password!")	    	
	return render_template('login.html', form = form, user = g.user)

# Logout page
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('index'))

# Will redirect to /index
@app.route('/')
def mainPage():
    return redirect(url_for('index'))

# Hard-coding list for top 10 rated movies in dashboard
top10_movies = [('Ghost Dog: The Way of the Samurai (1999)', 3328, 'https://upload.wikimedia.org/wikipedia/en/a/a5/Ghost_Dog_film_poster.jpg'),
				('Inception (2010)', 79132,  'https://upload.wikimedia.org/wikipedia/en/7/7f/Inception_ver3.jpg'),
				('The Shawshank Redemption (1994)', 318, 'https://upload.wikimedia.org/wikipedia/en/8/81/ShawshankRedemptionMoviePoster.jpg'),
				('Seven Samurai (1954)', 2019, 'https://upload.wikimedia.org/wikipedia/en/8/84/Seven_Samurai_movie_poster.jpg'),
				('The Usual Suspects (1995)', 50, 'https://upload.wikimedia.org/wikipedia/en/9/9c/Usual_suspects_ver1.jpg'),
				('Ran (1985)', 1217, 'https://upload.wikimedia.org/wikipedia/en/f/f2/Kuroran.jpg'),
				('City of God (2002)', 6016,'https://upload.wikimedia.org/wikipedia/en/1/10/CidadedeDeus.jpg'),
				('My Neighbor Totoro (1988)', 5971, 'https://upload.wikimedia.org/wikipedia/en/0/02/My_Neighbor_Totoro_-_Tonari_no_Totoro_%28Movie_Poster%29.jpg'),
				('Lawrence of Arabia (1962)',1204, 'https://upload.wikimedia.org/wikipedia/commons/c/c5/Lawrence_of_arabia_ver3_xxlg.jpg'),
				('The Godfather (1972)', 858, 'https://upload.wikimedia.org/wikipedia/en/1/1c/Godfather_ver1.jpg')]

# Actual main page
# Provide link to recommendation, query by id(not usually used), query by name, and query by genre
@app.route('/index', methods=['GET', 'POST'])
def index():
	user = g.user
	if request.method == "POST":
    	# Search by name
		movie_id = request.form['name']
		if movie_id.isdigit():
			id = int(movie_id)
			movie = db.session.query(Movie).filter_by(id= id).first()
			if not movie:
				flash('Movie not found')
			else:
				return redirect(url_for('movie', movie_id = id))
				
		# Search by id
		else:
			movie = db.session.query(Movie).filter_by(title = movie_id).first()
			if not movie:
				flash('Movie not found')
			else:
				return redirect(url_for('movie', movie_id = movie.id))
	return render_template('index.html', movies = random.sample(top10_movies, 3), user = user)

# Info page for the movie db
@app.route('/details', methods = ['GET'])
def details():
    return render_template('explanation.html', user = g.user)

#
# Query use join based on 2 subqueies
@app.route('/movie/<movie_id>', methods=['GET', 'POST'])
def movie(movie_id):
	q1 = db.session.query(Movie.id.label("id"), 
						  Movie.title.label("title"), 
						  Movie.year.label("year"), 
						  Links.imdb_link.label("imdb"), 
						  Links.moviedb_link.label("moviedb"), 
						  Links.web_link.label("link")).\
						  join(Links, Links.movie_id == Movie.id).\
						  filter(Movie.id == movie_id).subquery()

	q2 = db.session.query(func.avg(Rating.score).label('avg_score'), 
						  func.count(Rating.score).label('reviews'), 
						  q1.c.id.label("id"),
						  q1.c.title.label("title"), 
						  q1.c.year.label("year"), 
						  q1.c.imdb.label("imdb"),
						  q1.c.moviedb.label("moviedb"), 
						  q1.c.link.label("link")).\
						  join(q1, q1.c.id == Rating.movie_id).\
						  group_by(Rating.movie_id).subquery()

	movie = db.session.query(Category.category, 
							 q2.c.id, 
							 q2.c.title, 
							 q2.c.year, 
							 q2.c.imdb, 
							 q2.c.moviedb, 
							 q2.c.avg_score, 
							 q2.c.reviews, 
							 q2.c.link).\
							 join(q2, q2.c.id==Category.movie_id).all()

	return render_template('movie.html', id = movie_id, movie=movie, user = g.user)

# Search page
# User need to constrain which genre (at least one), movie year and review score/number
@app.route('/search', methods = ['GET', 'POST'])
def search_movie():
	movies = []
	if request.method == "POST":
		genres = request.form.getlist('checkboxArray[]')
		years = request.form['year'].split(" - ")
		score = request.form['score']
		reviews = request.form['reviews']

		subq = db.session.query(Category.movie_id.label('id')).\
			   group_by(Category.movie_id).\
			   filter(Category.category.in_(genres)).\
			   having(func.count(Category.category)==len(genres)).subquery()

		ratings = db.session.query(Rating.movie_id.label('id'), 
								   func.avg(Rating.score).label('avg_score'), 
								   func.count(Rating.score).label('reviews')).\
								   join(subq, subq.c.id==Rating.movie_id).\
								   group_by(Rating.movie_id).subquery()

		movies = db.session.query(Movie.id.label('id'), 
								  Movie.title.label('title'), 
								  Movie.year.label('year'), 
								  ratings.c.avg_score.label('score'), 
								  ratings.c.reviews.label('reviews')).\
								  join(ratings, ratings.c.id == Movie.id).\
								  filter(ratings.c.avg_score >= float(score)).\
								  filter(ratings.c.reviews >= int(reviews)).\
								  filter(and_(Movie.year >= int(years[0]), Movie.year <= int(years[1]))).\
								  order_by(ratings.c.avg_score.desc()).all()
		
		if movies == []:
			flash('No Movie found!')
		return render_template('search.html', data = movies, genres = genres, num = len(movies), user = g.user)
	return render_template('search.html', data = movies, genres = [], num = 0, user = g.user)

# Ranking by style
@app.route('/style/<style>', methods = ['GET'])
def style(style):
	style = style.capitalize()

	# correct certain genre names
	if style == 'Imax':
		style = 'IMAX'
	elif style == 'Sci-fi':
		style = 'Sci-Fi'
	elif style == 'Film-noir':
		style = 'Film-Noir'

	q1 = db.session.query(Category.movie_id.label('id'),
					      func.avg(Rating.score).label('score'), 
					      func.count(Rating.score).label('reviews')).\
						  filter_by(category=style).\
						  join(Rating, Rating.movie_id==Category.movie_id).\
						  group_by(Rating.movie_id).having(func.count(Rating.score) > 10).\
						  order_by(func.avg(Rating.score).desc()).limit(20).subquery()

	movies = db.session.query(Movie.title, Movie.year, q1.c.score, q1.c.reviews, Movie.id).join(q1, q1.c.id == Movie.id).all()
	return render_template('style.html', movies = movies, style = style, user = g.user)

@app.route('/browse/<style>/<p>', methods=['GET', 'POST'])
def browse(style, p):
	offset = 20*(int(p)-1)
	if style == 'id':
		order = Movie.id
	elif style == 'title':
		order = Movie.title
	elif style == 'year':
		order = Movie.year.desc()
	elif style == 'score':
		order = func.avg(Rating.score).desc()
	else:
		order = func.count(Rating.score).desc()
	movies = db.session.query(Movie.id, 
			  				  Movie.title, 
			  				  Movie.year, 
			  				  func.avg(Rating.score), 
			  				  func.count(Rating.score)).\
			 				  join(Rating, Rating.movie_id == Movie.id).\
			 				  group_by(Rating.movie_id).\
			 				  order_by(order).offset(offset).limit(20).all()
	return render_template('browse.html', style = style, page = int(p), movies = movies, user = g.user)

# Recommendation module
@app.route('/recommend', methods = ['GET', 'POST'])
@login_required
def recommend():
	user = g.user

	cid = user._id+1000
	if request.method == "POST":
		# Method for add movie
		# Every time insert movie into sql if haven't recommended before
		# Else inform user that this movie has already been recommended
		if request.form['submit'] == "Add movie":
			title = request.form['movie_name']
			score = request.form['score']
			movie = db.session.query(Movie).filter_by(title = title).first()
			if movie == None:
				flash('Movie not found!')
			else:	
				checks = db.session.query(Rating).filter_by(user_id = cid).filter(Rating.movie_id == movie.id).all()
				if (len(checks) > 0):
					flash('Duplicate rating!')
				else:
					rating = models.Rating(user_id = cid,
                           movie_id = movie.id,
                           score = score,
                           time = datetime.now())
					
					db.session.add(rating)
					db.session.commit()
			redirect(url_for('recommend'))
		if request.form['submit'] == "Clear":
			categories = models.Rating.query.filter_by(user_id = cid).all()
			for r in categories:
				db.session.delete(r)
			db.session.commit()
			return redirect(url_for('recommend'))


		if request.form['submit'] == "Recommend!":
			categories = models.Rating.query.filter_by(user_id = cid).all()

			# At least rate 3 movies to get user-based recommendation 
			if (len(categories) < 3):
				flash('Too less reviews!')
				return redirect(url_for('recommend'))

			# use rec module to get recommendation
			matrix, urate, avg, dics = rec.prepare(rec.rating)
			new_user = np.zeros(matrix[0].size)
			for r in categories:
				cid = r.movie_id
				new_user[dics[cid]] = r.score
				#clean the record to be ready for another recommendation
				'''Now we don't need to clean the database upon recommendation. The data will be
					stored in db unless the user choose to delete.
				'''
				#db.session.delete(r)
			#db.session.commit()
			ans = rec.predict(new_user, matrix, urate, avg, N=100)
			ids = [int(ans[i][1]) for i in range(len(ans))]
			return redirect(url_for('recommend_result', rec = ids))
	ratings = db.session.query(Rating.movie_id, 
							   Movie.title,
							   Movie.year, 
							   Rating.score).\
							   filter_by(user_id = cid).\
							   join(Movie, Movie.id == Rating.movie_id).all()

	return render_template('recommend.html', ratings = ratings, user = g.user)

# Recommendation result page
# List in table 
# Can acutally set number of movies to show in previous page
@app.route('/recommend_result/<rec>', methods = ['GET'])
def recommend_result(rec):
	res = ''.join(rec[1:-1]).split(',')

	movies = db.session.query(Movie.id, 
			  				  Movie.title, 
			  				  Movie.year, 
			  				  func.avg(Rating.score), 
			  				  func.count(Rating.score)).\
			 				  filter(Movie.id.in_(res)).\
			 				  join(Rating, Rating.movie_id == Movie.id).\
			 				  group_by(Rating.movie_id).all()

	return render_template('rec_result.html',  movies = movies, user = g.user)

# Autocompelete module by preloading
@app.route('/autocomplete',methods=['GET'])
def autocomplete():

    search = request.args.get('term')
    NAMES = db.session.query(Movie).all()

    return jsonify(json_list=[i.title for i in NAMES]) 