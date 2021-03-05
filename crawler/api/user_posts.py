from crawler.api import bp
from flask import request
from scrapy.crawler import CrawlerProcess
from crawler.InstagramCrawler.spiders import instagram


@bp.route('/user_posts', method=['POST'])
def get_user_posts():
