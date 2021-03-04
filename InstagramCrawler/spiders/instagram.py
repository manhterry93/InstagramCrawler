import scrapy
from InstagramCrawler.base import constants
import json
from InstagramCrawler.util import util
from scrapy.http import FormRequest

class InstagramSpider(scrapy.Spider):
    name = "instagram"

    def __init__(self):
        self.header = {"Referer": constants.BASE_URL}
        self.username = 'hacwick@gmail.com'
        self.password = 'abcd@1234'

    def start_requests(self):
        # Goto instagram.com for getting x-crsf token
        print('start request')
        self.header[
            'user-agent'] = constants.STORIES_UA
        yield scrapy.Request(constants.BASE_URL, callback=self.parse, headers=self.header, meta={
            'dont_redirect': True,
            'handle_httpstatus_list': [302]
        })

    def parse(self, response):
        content = response.body_as_unicode()
        list_cookies = response.headers.getlist('Set-Cookie')
        csrftoken = util.extract_csrftoken_from_cookies(list_cookies)
        print('crsftoken: ', csrftoken)

        # print('set-cookie: ', list_cookies)
        if not csrftoken:
            # Token not found-> do nothing
            return
        else:
            # Update crsf token to header
            self.header["X-CSRFToken"] = csrftoken
            # After got token,
            body = {'username': self.username, 'password': self.password}
            self.header["Referer"] = "https://www.instagram.com/accounts/login/"
            self.header["x-requested-with"] = "XMLHttpRequest"
            yield scrapy.FormRequest(constants.LOGIN_URL, formdata=body, headers=self.header,
                                 callback=self.parse_login, )
        # extract crsftoken

    def parse_login(self, response):
        # print('Login response: ', json.dumps(response.headers.to_unicode_dict()))
        print('login text: ', response.body_as_unicode())
