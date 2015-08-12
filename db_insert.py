from app import db, models
from app.views import preprocess
from datetime import datetime
import csv
import string


def isFloat(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def bracket(s):
    s_new = preprocess(s)
    for i in range(len(s_new)-1, -1, -1):
        if s_new[i] == '(':
            return (s_new, i)
    return (s_new, len(s_new))

def main():
    with open("./app/data/movies.csv") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        i = 0
        for data in reader:
            i += 1
            #print i
            if i == 1:
                continue
            br = bracket(data[1])
            mov = models.Movie(id = int(data[0]),
                             title = br[0][0: br[1]],
                             year = int(br[0][br[1]+1: br[1]+5]) if br[1] < len(br[0]) else 2011)
            genres = data[2].split('|')
            print mov.id, mov.year, mov.title
            for genre in genres:
                if genre != '(no genres listed)':
                    gre = models.Category(movie_id = int(data[0]),  category = preprocess(genre))
                    print gre.movie_id, gre.category
                db.session.add(gre)
            db.session.add(mov)
            if i % 1000 == 0:
                db.session.flush()
        db.session.commit()

    with open("./app/data/links.csv") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        i = 0
        for data in reader:
            i += 1
            print i
            if i == 1:
                continue
            link = models.Links(movie_id = int(data[0]),
                               imdb_link = int(data[1] if data[1].isdigit() else None),
                               moviedb_link = int(data[2]) if data[2].isdigit() else None)
            #print link.movie_id. link.imdb_link, link.moviedb_link
            db.session.add(link)
            if i % 1000 == 0:
                db.session.flush()
        db.session.commit()

    with open("./app/data/ratings.csv") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        i = 0
        for data in reader:
            i += 1
            #print i
            if i == 1:
                continue
            rating = models.Rating(user_id = int(data[0]),
                               movie_id = int(data[1]),
                               score = float(data[2])*1.0,
                               time = datetime.fromtimestamp(int(data[3])))
            print rating.user_id, rating.movie_id, rating.score, rating.time
            db.session.add(rating)
            if i % 1000 == 0:
                db.session.flush()
        db.session.commit()



if __name__ == '__main__':
    main()

    
