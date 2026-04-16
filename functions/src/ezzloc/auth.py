import hashlib
import datetime
import requests
from src.ezzloc.config import USERNAME, PASSWORD, LOGIN_URL, LANGUAGE_TYPE_VALUE


class EzzlocAuth:
    def __init__(self, username=None, password=None):
        self.username = username or USERNAME
        self.password = password or PASSWORD
        self.token = None

    def login(self):
        """Authenticate and obtain access token."""
        # Hash password using simple MD5 (matching test fix)
        hashed_password = hashlib.md5(self.password.encode('utf-8')).hexdigest()

        payload = {
            "username": self.username,
            "password": hashed_password,
            "languageTypeValue": LANGUAGE_TYPE_VALUE
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(LOGIN_URL, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        # print(f"Ezzloc auth response: {data}")

        # Check response format - might need to handle different structures
        if data.get("code") == 200:  # Assuming 200 means success
            # Token might be in headers, cookies, or different field
            self.token = (data.get("token") or
                         data.get("access_token") or
                         data.get("data"))
        else:
            raise ValueError(f"Login failed: {data.get('msg', 'Unknown error')}")

        if not self.token:
            # Check cookies if no token in response
            self.token = response.cookies.get("token") or response.cookies.get("auth_token")
            if not self.token:
                raise ValueError("Login failed: No token found in response or cookies")

        return self.token
