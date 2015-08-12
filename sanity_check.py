from app import db, models

def main():
	movies = models.Movie.query.all()

	for r in movies:
	    print r.id, r.year, r.title


	categories = models.Category.query.all()

	for r in categories:
	    print r.movie_id, r.category



	movies = models.Links.query.all()

	for r in movies:
	    print r.movie_id, r.imdb_link, r.moviedb_link


	categories = models.Rating.query.all()

	for r in categories:
	    print r.user_id, r.movie_id, r.score


if __name__ == '__main__':
    main()