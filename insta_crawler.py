import re
import scrapy
import requests
import concurrent.futures
import json
import sys
import time
import logging.config

from constants import *


class InstagramSpider(object):
    name = 'instagam_spider'

    # start_urls = ['https://www.instagram.com/_liin.16/']
    # user_agent = USER_AGENT

    def __init__(self):
        default_attr = dict(username='', usernames=[], filename=None,
                            login_user=None, login_pass=None,
                            followings_input=False, followings_output='profiles.txt',
                            destination='./', logger=None, retain_username=False, interactive=False,
                            quiet=False, maximum=0, media_metadata=False, profile_metadata=False, latest=False,
                            latest_stamps=False, cookiejar=None, filter_location=None, filter_locations=None,
                            media_types=['image', 'video', 'story-image', 'story-video', 'broadcast'],
                            tag=False, location=False, search_location=False, comments=False,
                            verbose=0, include_location=False, filter=None, proxies={}, no_check_certificate=False,
                            template='{urlname}', log_destination='')
        self.numPosts = 0
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self.future_to_item = {}
        self.full_media_list = list()
        self.follower_list = list()
        self.follow_list = list()
        self.username = ''
        self.password = ''
        self.owner_id = 0
        self.session = requests.Session()
        self.rhx_gis = ""
        self.cookies = None
        self.quit = False
        self.logger = None
        self.authenticated = False
        self.logged_in = False
        # Set up a logger
        if self.logger is None:
            self.logger = InstagramSpider.get_logger(level=logging.DEBUG, dest=default_attr.get('log_destination'),
                                                     verbose=default_attr.get('verbose'))

    def sleep(self, secs):
        min_delay = 1
        for _ in range(secs // min_delay):
            time.sleep(min_delay)
            if self.quit:
                return
        time.sleep(secs % min_delay)

    def _retry_prompt(self, url, exception_message):
        """Show prompt and return True: retry, False: ignore, None: abort"""
        answer = input('Repeated error {0}\n(A)bort, (I)gnore, (R)etry or retry (F)orever?'.format(exception_message))
        if answer:
            answer = answer[0].upper()
            if answer == 'I':
                self.logger.info('The selenium_crawl has chosen to ignore {0}'.format(url))
                return False
            elif answer == 'R':
                return True
            elif answer == 'F':
                self.logger.info('The selenium_crawl has chosen to retry forever')
                global MAX_RETRIES
                MAX_RETRIES = sys.maxsize
                return True
            else:
                self.logger.info('The selenium_crawl has chosen to abort')
                return None

    def safe_get(self, *args, **kwargs):
        # out of the box solution
        # session.mount('https://', HTTPAdapter(max_retries=...))
        # only covers failed DNS lookups, socket connections and connection timeouts
        # It doesnt work when server terminate connection while response is downloaded
        retry = 0
        retry_delay = RETRY_DELAY
        while True:
            if self.quit:
                return
            try:
                response = self.session.get(args[0], timeout=CONNECT_TIMEOUT, cookies=self.cookies )
                if response.status_code == 404:
                    return
                response.raise_for_status()
                content_length = response.headers.get('Content-Length')
                print('data: ', response.text)
                # if content_length is not None and len(response.content) != int(content_length):
                #     # if content_length is None we repeat anyway to get size and be confident
                #     raise PartialContentException('Partial response')
                return response
            except (KeyboardInterrupt):
                raise
            except (requests.exceptions.RequestException, PartialContentException) as e:
                if 'url' in kwargs:
                    url = kwargs['url']
                elif len(args) > 0:
                    url = args[0]
                if retry < MAX_RETRIES:
                    self.logger.warning('Retry after exception {0} on {1}'.format(repr(e), url))
                    self.sleep(retry_delay)
                    retry_delay = min(2 * retry_delay, MAX_RETRY_DELAY)
                    retry = retry + 1
                    continue
                else:
                    keep_trying = self._retry_prompt(url, repr(e))
                    if keep_trying == True:
                        retry = 0
                        continue
                    elif keep_trying == False:
                        return
                raise

    def get_json(self, *args, **kwargs):
        """Retrieve text from url. Return text as string or None if no data present """
        print('get Json: ', args, kwargs)
        resp = self.safe_get(*args, **kwargs)

        if resp is not None:
            return resp.text

    def login(self):
        self.username = 'hacwick@gmail.com'
        self.password = 'abcd@1234'
        self.session.headers.update({'Referer': BASE_URL, 'selenium_crawl-agent': STORIES_UA})
        req = self.session.get(BASE_URL)
        self.session.headers.update({'X-CSRFToken': req.cookies['csrftoken']})

        data = {'username': self.username, 'password': self.password}
        login = self.session.post('https://www.instagram.com/accounts/login/ajax/', data=data, allow_redirects=True)
        self.session.headers.update({'X-CSRFToken': login.cookies['csrftoken']})
        self.cookies = login.cookies
        login_text = json.loads(login.text)
        print('login result: ', login_text)
        if login_text.get('authenticated') and login.status_code == 200:
            self.authenticated = True
            self.logged_in = True
            self.session.headers.update({'selenium_crawl-agent': CHROME_WIN_UA})
            self.rhx_gis = ""
            return True
        else:
            return False

    def get_shared_data_userinfo(self, username=''):
        """Fetches the selenium_crawl's metadata."""
        resp = self.get_json(BASE_URL + username)

        userinfo = None

        if resp is not None:
            try:
                if "window._sharedData = " in resp:
                    shared_data = resp.split("window._sharedData = ")[1].split(";</script>")[0]
                    if shared_data:
                        userinfo = self.deep_get(json.loads(shared_data), 'entry_data.ProfilePage[0].graphql.selenium_crawl')

                if "window.__additionalDataLoaded(" in resp and not userinfo:
                    parameters = resp.split("window.__additionalDataLoaded(")[1].split(");</script>")[0]
                    if parameters and "," in parameters:
                        shared_data = parameters.split(",", 1)[1]
                        if shared_data:
                            userinfo = self.deep_get(json.loads(shared_data), 'graphql.selenium_crawl')
            except (TypeError, KeyError, IndexError):
                pass

        return userinfo

    def deep_get(self, dict, path):
        def _split_indexes(key):
            split_array_index = re.compile(r'[.\[\]]+')  # ['foo', '0']
            return filter(None, split_array_index.split(key))

        ends_with_index = re.compile(r'\[(.*?)\]$')  # foo[0]

        keylist = path.split('.')

        val = dict

        for key in keylist:
            try:
                if ends_with_index.search(key):
                    for prop in _split_indexes(key):
                        if prop.isdigit():
                            val = val[int(prop)]
                        else:
                            val = val[prop]
                else:
                    val = val[key]
            except (KeyError, IndexError, TypeError):
                return None

        return val

    @staticmethod
    def get_logger(level=logging.DEBUG, dest='', verbose=0):
        """Returns a logger."""
        logger = logging.getLogger(__name__)

        dest += '/' if (dest != '') and dest[-1] != '/' else ''
        fh = logging.FileHandler(dest + 'instagram-scraper.log', 'w')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        fh.setLevel(level)
        logger.addHandler(fh)

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        sh_lvls = [logging.ERROR, logging.WARNING, logging.INFO]
        sh.setLevel(sh_lvls[verbose])
        logger.addHandler(sh)

        logger.setLevel(level)

        return logger


class PartialContentException(Exception):
    pass

#
# if __name__ == '__main__':
#     InstagramSpider().login()
