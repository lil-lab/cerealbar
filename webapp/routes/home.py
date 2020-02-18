import sqlite3
import hashlib
from flask import Blueprint, render_template, request

import webapp.database as db
from webapp.config import DATABASE_NAME

home = Blueprint('home', __name__)


@home.route("/")
def web_app():
    db.write_raw_client(str(hashlib.md5(request.environ['REMOTE_ADDR'].encode('utf-8')).hexdigest()),
                        request.environ[
        'REMOTE_PORT'])
    return render_template("index.html", leaders=get_leaderboard(100))


def get_leaderboard(size):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()
    q = 'SELECT score FROM games'
    c.execute(q)
    scores = list(c.fetchall())
    scores = [x[0] for x in scores]
    scores = [x for x in scores if x is not None]
    scores = sorted(scores, reverse=True)
    db.close()
    ret = []
    for i in range(0, min(len(scores), size)):
        ret.append([i+1, scores[i]])
    return ret
