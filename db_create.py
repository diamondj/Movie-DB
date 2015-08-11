#!flask/bin/python
from app import db, manager
db.create_all()

if __name__ == '__main__':
    manager.run()
