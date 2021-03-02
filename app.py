# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from insta_crawler import InstagramSpider


def main():
    print('main')
    scraper = InstagramSpider()
    login_success = scraper.login()
    if login_success:
        # login success, load user detail
        sharedData = scraper.get_shared_data_userinfo("_liin.16")
        print('shared Data: \n', sharedData)

if __name__ == '__main__':
    main()
