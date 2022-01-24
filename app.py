#!/usr/bin/env python

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap


# App config and database instance.
app = Flask(__name__)  # application instance
app.config['SECRET_KEY'] = "b'_5#y2L'F4Q8z\n\xec]/'"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/nettool__db.db'  # path to database and its name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # to supress warning
Bootstrap(app)  # initialize bootstrap support
db = SQLAlchemy(app)  # database instance


# Create login_manager
login_manager = LoginManager()
# Initialize login_manager
login_manager.init_app(app)

import models
import routes

if __name__ == "__main__":
    #db.create_all()
    app.run(debug=True)
