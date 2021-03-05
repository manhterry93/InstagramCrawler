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
        self.user_id = ""

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
        response_dict = json.loads(response.body_as_unicode())
        print('login text: ', response_dict)
        if response_dict["authenticated"] == True:
            # login success => loading post
            self.header.pop("x-requested-with")
            self.header["Referer"] = constants.BASE_URL + "_liin.16/"

            yield scrapy.Request(constants.BASE_URL + "_liin.16/", callback=self.parse_shared_data,
                                 headers=self.header)

    def parse_shared_data(self, response):
        response_body = response.body_as_unicode()

        # Split window._sharedData
        shared_data = json.loads(response_body.split("window._sharedData = ")[1].split(";</script>")[0])
        posts = shared_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]

        f = open('shit.txt', "a")
        f.write(json.dumps(shared_data))
        f.close()
        print('shared text: ', posts)

        # paging
        user_id = shared_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["id"]
        self.user_id = user_id
        if posts["page_info"]["has_next_page"] == True:
            end_cursor = posts["page_info"]["end_cursor"]
            var = util.build_posts_query_variable(user_id=user_id, after_token=end_cursor)
            yield scrapy.Request(constants.POSTS_QUERY.format(var), headers=self.header,
                                 callback=self.parse_post_paging)

    def parse_post_paging(self, response):
        response_body = json.loads(response.body_as_unicode())

        if response_body["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]["has_next_page"] == True:
            end_cursor = response_body["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]["end_cursor"]
            var = util.build_posts_query_variable(user_id=self.user_id, after_token=end_cursor)
            yield scrapy.Request(constants.POSTS_QUERY.format(var), headers=self.header,
                                 callback=self.parse_post_paging)
        print('shared text: ', response_body)
