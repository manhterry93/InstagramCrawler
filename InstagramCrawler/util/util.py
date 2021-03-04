
def extract_csrftoken_from_cookies(list_cookies):
    for cookie in list_cookies:
        decoded = cookie.decode('utf-8')
        # remove ";"
        decoded = decoded.split(";")[0]
        if decoded.startswith("csrftoken"):
            token = decoded.split("=")[1]
            return token
    return None


