from app import db, models

def main():
    movies = models.Movie.query.all()
    i = 1
    for r in movies:
        print r.id, r.year, r.title
        db.session.delete(r)
        if i%1000 == 0:
        	db.session.flush()
        i += 1
    db.session.commit()

    categories = models.Category.query.all()
    i = 1
    for r in categories:
        print r.movie_id, r.category
        db.session.delete(r)
        if i%1000 == 0:
        	db.session.flush()
        i += 1
    db.session.commit()


    movies = models.Links.query.all()
    i = 1
    for r in movies:
        print r.movie_id, r.imdb_link, r.moviedb_link
        db.session.delete(r)
        if i%1000 == 0:
            db.session.flush()
        i += 1
    db.session.commit()

    categories = models.Rating.query.all()
    i = 1
    for r in categories:
        print r.user_id, r.movie_id, r.score
        db.session.delete(r)
        if i%1000 == 0:
            db.session.flush()
        i += 1
    db.session.commit()


if __name__ == '__main__':
    main.run()
