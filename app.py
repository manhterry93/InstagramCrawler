# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from insta_crawler import InstagramSpider
import json
from selenium_crawl import instagram_crawler
import logging


def main():
    print('main')
    scraper = InstagramSpider()
    login_success = scraper.login()
    if login_success:
        # login success, load selenium_crawl detail
        sharedData = scraper.get_shared_data_userinfo("_liin.16")
        print('shared Data: \n', json.dumps(sharedData))


if __name__ == '__main__':
    instagram_crawler.process_for_cookies(logging, False)
    # main()
