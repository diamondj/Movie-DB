from hashlib import md5
from app import db, manager
from flask import jsonify

class Movie(db.Model):
    __tablename__ = 'movie'
   
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(128), nullable=False)
    year = db.Column(db.Integer)
    rating = db.relationship("Rating",  backref=db.backref('movie', uselist = True, lazy='dynamic'))
    category = db.relationship("Category",  backref=db.backref('movie', uselist = True, lazy='dynamic'))
    links = db.relationship("Links", backref=db.backref('movie'))

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id' : self.id,
           'title' : self.title,
           'year' : self.year,          
       }
 
class Rating(db.Model):
    __tablename__ = 'rating'

    
    _id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    score = db.Column(db.Float(precision = 2), nullable = False)
    time = db.Column(db.DateTime)
    

    @property
    def serialize(self):
       
       return {
           'id'         : self._id,
           'user_id'         : self.user_id,
           'movie_id'         : self.movie_id,
           'score'       : self.score,
           'review_time'       : self.time,
       }

    def __repo__(self):
      return "User:"+unicode(self.user_id) + " rates movie #" + self.movie_id + " with score of " + unicode(self.score)

class Category(db.Model):
    __tablename__ = 'category'

    _id = db.Column(db.Integer, primary_key = True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    category = db.Column(db.String(128), nullable=False)  
    @property
    def serialize(self):  
       return {
           'id'         : self._id,
           'movie_id'         : self.movie_id,
           'category'       : self.category,
       }

class Links(db.Model):
    __tablename__ = 'links'
    _id = db.Column(db.Integer, primary_key = True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    imdb_link = db.Column(db.String(128))
    moviedb_link = db.Column(db.String(128))
    web_link =  db.Column(db.String(128))
    @property
    def serialize(self):  
       return {
           'id'         : self.movie_id,
           'imdb_link'         : self.imdb_link,
           'moviedb_link'       : self.moviedb_link,
       }


if __name__ == '__main__':
    manager.run()
