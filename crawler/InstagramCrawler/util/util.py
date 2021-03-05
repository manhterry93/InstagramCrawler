import json


def extract_csrftoken_from_cookies(list_cookies):
    for cookie in list_cookies:
        decoded = cookie.decode('utf-8')
        # remove ";"
        decoded = decoded.split(";")[0]
        if decoded.startswith("csrftoken"):
            token = decoded.split("=")[1]
            return token
    return None


def build_posts_query_variable(user_id, after_token, amount=12):
    return json.dumps({
        "id": user_id,
        "first": amount,
        "after": after_token})
