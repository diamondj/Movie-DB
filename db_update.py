from app import db, models
from app.views import preprocess
from datetime import datetime
import csv


def main():
    with open("./app/data/header.csv") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        i = 0
        for data in reader:
            i += 1
            print i
            if i == 1:
                continue

            links = models.Links.query.filter(models.Links.moviedb_link == data[0]).first()
            if links != None:
                links.web_link = data[1]
                db.session.commit()

if __name__ == '__main__':
    main()



    
