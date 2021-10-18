# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire import webdriver
from selenium.webdriver.common import by
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
import json
import time
import pickle
import os.path
import traceback
# must import below
import logging
import chromedriver_binary

COOKIE_PATH = 'insta_cookies_scrapy'
LOGIN_ACCOUNTS = "instagram_account.json"
HOME_URL = "https://www.instagram.com"


def parse_body(body_string):
    body = {}
    temps = body_string.split('&')
    for temp in temps:
        key_value = temp.split('=')
        body[key_value[0]] = key_value[1]
    return body


def process_for_cookies(logger, driver=None, headless=True):
    """
    Use selenium for getting Instagram session cookies
    :param driver: Webchrome driver
    :param url:
    :param logger:
    :param headless:
    :return:
    """
    print("----Process for cookie")
    if not driver:
        # init Chrome driver (Selenium)
        options = Options()
        # options.add_experimental_option('w3c', False)  ### added this line
        # options.headless = True
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument('ignore-certificate-errors')
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        # cap = DesiredCapabilities.CHROME
        # cap["loggingPrefs"] = {"performance": "ALL"}
        options.add_experimental_option("detach", True)  # prevent browser close
        ### installed chromedriver.exe and identify path
        driver = webdriver.Chrome(
            options=options)  ### installed

    accounts = load_accounts(logger)

    if not accounts:
        logger.info("Load accounts failed")
        return None
    user_name, pwd, account_position = get_account(logger, accounts, 0)
    try:
        # record and parse performance log
        driver.get(HOME_URL)
        try:
            load_cookie(driver, COOKIE_PATH)
        except Exception as ex:
            if logger:
                logger.error('load cookie failed: {}'.format(ex))
            print('load cookie failed: ', ex)

        time.sleep(2)  # Wait 2s after update cookie
        driver.get(HOME_URL)

        print('url after cookie: ', driver.current_url)
        if logger:
            logger.info("url after cooking: {}".format(driver.current_url))
        if 'checkpoint' in driver.current_url or 'challenge' in driver.current_url:
            # Authorized failed, Clear cookie first
            if logger:
                logger.info('Authorized failed for exist cookie, clearing cookie.....')
            print('Authorized failed for exist cookie, clearing cookie.....')
            clear_cookie(driver, COOKIE_PATH)
            update_account_list(accounts, account_position, True)
            driver.get(HOME_URL)
            time.sleep(2)
            if account_position < len(accounts) - 1:
                return process_for_cookies(logger, driver, headless)
            else:
                return False

        # check if loggedin or not
        emails = driver.find_elements(by=by.By.XPATH, value='//*[@id="loginForm"]')
        if len(emails) == 0:
            # DOn't need to re-login
            if logger:
                logger.info('Logged in already')
            print('Logged in already')
            print('current url: ', driver.current_url)
        else:
            print('Need login')
            if logger:
                logger.info('Need login')
            email = driver.find_element(by=by.By.NAME, value='username')
            print('email: ', email)
            email.click()
            email.send_keys(user_name)

            password = driver.find_element(by=by.By.NAME, value='password')
            password.click()
            password.send_keys(pwd)

            login_btn = driver.find_element(by=by.By.CLASS_NAME, value='L3NKy')
            time.sleep(1)
            login_btn.click()
            if logger:
                logger.info('After click login button')
            print('click login button')
        time.sleep(5)
        if 'checkpoint' in driver.current_url or 'challenge' in driver.current_url:
            # Double check for banned account
            # Is banned, Stop loading, throw Exception,
            logger.info("Unauthorized account")
            print('Unauthorized account')
            clear_cookie(driver, COOKIE_PATH)
            update_account_list(accounts, account_position, True)
            if account_position < len(accounts) - 1:
                return process_for_cookies(logger, driver, headless)
            else:
                return False
        # time.sleep(2)
        # driver.get(HOME_URL)

        print('current_url', driver.current_url)
        if 'accounts/onetap' in driver.current_url:
            # Save information
            try:
                save_info_btn = driver.find_elements(by=by.By.CLASS_NAME, value='L3NKy')
                if save_info_btn:
                    save_info_btn[0].click()
            except:
                print("click save info btn failed")
        time.sleep(2)
        driver.get(HOME_URL)
        if not len(emails) == 0:
            # We just save cookie if we need to login
            save_cookie(driver, COOKIE_PATH)
        return True
    except Exception as e:
        if logger:
            logger.info('Process for cookies failed')
        print('Process for cookies failed', e)
        return False
    # driver.quit()


def is_login_form_exist(driver, logger=None):
    emails = driver.find_elements(by=by.By.XPATH, value='//*[@id="loginForm"]')
    return len(emails) > 0


def save_cookie(driver, path):
    cookies = json.dumps(driver.get_cookies())
    with open(path, 'w') as filehandler:
        filehandler.write(cookies)


def clear_cookie(driver, path):
    driver.delete_all_cookies()
    if not os.path.isfile(path):
        return
    file = open(path, 'w')
    file.close()


def load_cookie(driver, path):
    # File not exist, return
    if not os.path.isfile(COOKIE_PATH):
        return

    with open(path, 'r') as cookiesfile:
        cookies_str = cookiesfile.read()
        if cookies_str:
            cookies = json.loads(cookies_str)
            for cookie in cookies:
                print('cookie: ', cookie)
                if 'sameSite' in cookie and cookie['sameSite'] == 'None':
                    cookie.pop('sameSite', None)
                driver.add_cookie(cookie)


# print(get_perf_log_on_load('/ChelseaFC'))

# if __name__=="__main__":
#     get_perf_log_on_load("/vozpage", headless=False, logger=None)


def load_accounts(logger):
    """
    load instagram account list in json object
    :param logger:
    :return:
    """
    print('load accounts list')
    # File not exist, return
    if not os.path.isfile(LOGIN_ACCOUNTS):
        return None

    accounts = None
    try:
        with open(LOGIN_ACCOUNTS, 'r') as f:
            accounts = json.load(f)
            f.close()
    except:
        if logger:
            logger.info('load account failed')
    return accounts


def get_account(logger, accounts, position=0):
    print('Pick an account')
    """
    get the valid account from accounts list
    :param logger:
    :param accounts:
    :param position:
    :return:
    """
    user_name = accounts[position].get("username")
    password = accounts[position].get("password")
    blocked = accounts[position].get("blocked")
    if blocked:
        logger.info("{} is blocked, skip to next if exist...".format(user_name))
        if position < len(accounts) - 1:
            return get_account(logger, accounts, position + 1)
    return user_name, password, position


def update_account_list(accounts, account_position, blocked):
    """
    Update block status for account in a specific position
    :param accounts:
    :param account_position:
    :param blocked:
    :return:
    """
    if blocked:
        accounts[account_position]["blocked"] = True
        with open(LOGIN_ACCOUNTS, 'w') as f:
            json.dump(accounts, f)
            f.close()
