from dotenv import load_dotenv
import os

load_dotenv()
api_host = os.environ.get("api-host")
api_qs = os.environ.get("api-qs")

def build_url(path):
    url = api_host + path + '?' + api_qs
    print('url: ' + url)
    return url