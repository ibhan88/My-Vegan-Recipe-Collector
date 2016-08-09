"""Vegan Recipes"""


from jinja2 import StrictUndefined

# from flask import Flask, render_template, redirect, request, flash, session
from flask import Flask, render_template
from flask_debugtoolbar import DebugToolbarExtension

# from model import connect_to_db, db
from model import *


app = Flask(__name__)

app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("home.html")


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()