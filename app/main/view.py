# encoding: utf-8

from flask import jsonify, g, render_template
from app.main import main_blueprint

@main_blueprint.route("/", methods=["GET"])
def index():
    return render_template("index.html")
