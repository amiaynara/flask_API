from flask import Flask
# this will contain all the routes that are related to 'user'

from app import app
from user.models import User

@app.route('/signup/user', methods=["GET"])
def signup():
    return User().signup()      # creates a class. 

