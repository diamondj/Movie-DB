from flask import render_template, flash, redirect, session, url_for, request, jsonify
from flask_bootstrap import Bootstrap
from datetime import datetime
from app import app, db, models
from .models import Movie, Rating, Category, Links
from sqlalchemy import desc, func, and_, or_
from sqlalchemy.orm import load_only
import string
import recommend_user as rec
import numpy as np
import random


# helper function
def preprocess(s):
    return unicode(s, errors='ignore').strip()

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
							  join(Rating, Rating.movie_id == q1.c.id).
							  group_by(Rating.movie_id).all()
	return jsonify(movies = movies)

# API intro and search page
@app.route('/movie/api', methods=['GET', 'POST'])
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
	return render_template('api.html')

# Will redirect to /index
@app.route('/')
def mainPage():
    return redirect(url_for('index'))

# Hard-coding list for top 10 rated movies in dashboard
top10_movies = [('Ghost Dog: The Way of the Samurai (1999)', 3328, 'https://upload.wikimedia.org/wikipedia/en/1/19/Ghost_Dog.jpg'),
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

    return render_template('index.html', movies = random.sample(top10_movies, 3))

# Info page for the movie db
@app.route('/details', methods = ['GET'])
def details():
    return render_template('explanation.html')

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

	return render_template('movie.html', id = movie_id, movie=movie)

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
		return render_template('search.html', data = movies, genres = genres, num = len(movies))
	return render_template('search.html', data = movies, genres = [], num = 0)

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
	return render_template('style.html', movies = movies, style = style)

# Recommendation module
@app.route('/recommend', methods = ['GET', 'POST'])
def recommend():
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
				checks = db.session.query(Rating).filter_by(user_id = 0).filter(Rating.movie_id == movie.id).all()
				if (len(checks) > 0):
					flash('Duplicate rating!')
				else:
					rating = models.Rating(user_id = 0,
                           movie_id = movie.id,
                           score = score,
                           time = datetime.now())
					db.session.add(rating)
					db.session.commit()
			ratings = db.session.query(Rating.movie_id, 
									   Movie.title, 
									   Movie.year, 
									   Rating.score).\
									   filter_by(user_id = 0).\
									   join(Movie, Movie.id == Rating.movie_id).all()
			return render_template('recommend.html', ratings = ratings)

		if request.form['submit'] == "Recommend!":
			categories = models.Rating.query.filter_by(user_id = 0).all()

			# At least rate 3 movies to get user-based recommendation 
			if (len(categories) < 3):
				flash('Too less reviews!')
				ratings = db.session.query(Rating.movie_id, Movie.title, Rating.score).filter_by(user_id = 0).join(Movie, Movie.id == Rating.movie_id).all()
				return render_template('recommend.html', ratings = ratings)

			# use rec module to get recommendation
			matrix, urate, avg, dics = rec.prepare(rec.rating)
			new_user = np.zeros(matrix[0].size)
			for r in categories:
				cid = r.movie_id
				new_user[dics[cid]] = r.score
				#clean the record to be ready for another recommendation
				db.session.delete(r)
			db.session.commit()
			ans = rec.predict(new_user, matrix, urate, avg, N=100)
			ids = [int(ans[i][1]) for i in range(len(ans))]
			return redirect(url_for('recommend_result', rec = ids))
	
	ratings = db.session.query(Rating.movie_id, 
							   Movie.title, 
							   Rating.score).\
							   filter_by(user_id = 0).\
							   join(Movie, Movie.id == Rating.movie_id).all()

	return render_template('recommend.html', ratings = ratings)

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

	return render_template('rec_result.html',  movies = movies)

# Autocompelete module by preloading
@app.route('/autocomplete',methods=['GET'])
def autocomplete():

    search = request.args.get('term')
    NAMES = db.session.query(Movie).all()

    return jsonify(json_list=[i.title for i in NAMES]) 