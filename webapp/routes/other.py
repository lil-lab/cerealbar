from flask import Blueprint, render_template

blank = Blueprint('blank', __name__, url_prefix="/home")


@blank.route("/")
def home():
    """Dummy home page"""
    return render_template("home.html")

