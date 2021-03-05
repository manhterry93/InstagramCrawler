from flask import Blueprint

bp = Blueprint('api', __name__)

from crawler.api import user_posts
