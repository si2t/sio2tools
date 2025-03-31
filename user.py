import urllib.parse

import requests
from errors import NoPasswordProvided, SessionObtainFailed
import bs4
import os
import json
import certifi

SIO2_BASEURL = "https://wyzwania.programuj.edu.pl/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"


class Auth:
    def __init__(
        self,
        username: str = None,
        password: str = None,
        csrftoken: str = None,
        sessionid: str = None,
    ):
        self.username = username
        self.password = password
        self.csrftoken = csrftoken
        self.sessionid = sessionid

    @property
    def cookie(self):
        return f"csrftoken={self.csrftoken}; sessionid={self.sessionid}; lang=en"

    @property
    def session_authenticated(self):
        return self.csrftoken and self.sessionid

    @property
    def password_authenticated(self):
        return self.username and self.password


class User:
    def __init__(self, auth: Auth, base_url: str | None):
        self.base_url = base_url or SIO2_BASEURL
        self.auth = auth

    def obtain_login_csrftoken(self):
        data = requests.get(self.base_url + "login/", {"User-Agent": USER_AGENT}, verify=certifi.where())
        soup = bs4.BeautifulSoup(data.text, "html.parser")
        csrftoken = soup.find("input", {"name": "csrfmiddlewaretoken"})
        general_csrf = data.cookies.get("csrftoken")
        return general_csrf, csrftoken.get("value")

    def obtain_session_credentials(self):
        if not self.auth.password_authenticated:
            raise NoPasswordProvided(
                "Username and password are required to obtain session credentials"
            )

        csrftoken, single_time_csrftoken = self.obtain_login_csrftoken()
        headers = {
            "User-Agent": USER_AGENT,
            "Authority": self.base_url.split("/", maxsplit=3)[2],
            "referer": self.base_url,
            "method": "POST",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-GB,en;q=0.6",
            "Cache-Control": "max-age=0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": f"lang=en; csrftoken={single_time_csrftoken}",
            "Upgrade-Insecure-Requests": "1",
            "Content-Length": "169",
        }
        data = requests.post(
            self.base_url + "login/",
            headers=headers,
            data={
                "login_view-current_step": "auth",
                "auth-username": self.auth.username,
                "auth-password": self.auth.password,
                "csrfmiddlewaretoken": single_time_csrftoken,
            },
            verify=certifi.where()
        )
        # print(data.text)
        self.auth.csrftoken = csrftoken
        self.auth.sessionid = data.cookies.get("sessionid")

        if not self.auth.session_authenticated:
            raise SessionObtainFailed("Failed to obtain session credentials")

    def fetch_sio2(self, path: str, method: str = "GET", data: dict | None = None, headers: dict | None = None):
        if headers is None:
            headers = {}
        if data is None:
            data = {}
        if path.startswith("/"):
            path = path[1:]
        if not path.startswith("http"):
            path = urllib.parse.urljoin(self.base_url, path)

        if not self.auth.session_authenticated:
            self.obtain_session_credentials()

        headers = {
            "Cookie": self.auth.cookie,
            "User-Agent": USER_AGENT,
            "Authority": self.base_url.split("/", maxsplit=3)[2],
            "referer": self.base_url,
            **headers,
        }
        # print(headers)
        data = requests.request(method, path, headers=headers, verify=certifi.where(), data=data)
        return data

    def _ensure_json_exists(self, path: str):
        if not os.path.exists(os.path.expanduser(path)):
            with open(os.path.expanduser(path), "w") as f:
                f.write("{}")

    def store_credentials(self, sio2url: str | None = None):
        self._ensure_json_exists("~/.sio2tools_credentials")
        if sio2url is None: sio2url = SIO2_BASEURL
        if not self.auth.session_authenticated:
            self.obtain_session_credentials()

        with open(os.path.expanduser("~/.sio2tools_credentials"), "r") as f:
            data = json.load(f)
        with open(os.path.expanduser("~/.sio2tools_credentials"), "w") as f:
            data[sio2url] = {
                "sessionid": self.auth.sessionid,
                "csrftoken": self.auth.csrftoken,
            }
            json.dump(data, f, indent=2)

    def remove_credentials(self):
        try:
            os.remove(os.path.expanduser("~/.sio2tools_credentials"))
        except FileNotFoundError:
            pass

    @classmethod
    def load_credentials_from_file(cls, sio2url: str | None):
        if sio2url is None: sio2url = "https://wyzwania.programuj.edu.pl/"
        try:
            with open(os.path.expanduser("~/.sio2tools_credentials"), "r") as f:
                data = json.load(f).get(sio2url, None)
                if data is None:
                    raise ValueError("No credentials found for this SIO2 URL, please use the login module with this URL first")
                return cls(
                    auth=Auth(sessionid=data["sessionid"], csrftoken=data["csrftoken"]),
                    base_url=sio2url
                )
        except:
            raise FileNotFoundError("No credentials file found")
