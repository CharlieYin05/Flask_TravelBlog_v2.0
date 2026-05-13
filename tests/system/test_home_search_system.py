import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from werkzeug.serving import make_server

from app.extensions import csrf, db, login
from app.forms import LogoutForm
from app.models import User
from app.routes import main_bp

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class LiveServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=0):
        super().__init__(daemon=True)

        self.server = make_server(host, port, app)
        self.host = host
        self.port = self.server.server_port

        self.context = app.app_context()
        self.context.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.context.pop()

class HomeSearchSystemTests(unittest.TestCase):

    def create_webdriver(self):
        browser = os.environ.get(
            "SELENIUM_BROWSER",
            ""
        ).lower().strip()

        def make_chrome():
            options = ChromeOptions()

            options.add_argument("--headless=new")
            options.add_argument("--window-size=1400,1000")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            options.add_argument(
                f"--user-data-dir="
                f"{os.path.join(self.browser_profile_dir, 'chrome')}"
            )

            return webdriver.Chrome(options=options)

        def make_edge():
            options = EdgeOptions()

            options.add_argument("--headless=new")
            options.add_argument("--window-size=1400,1000")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            options.add_argument(
                f"--user-data-dir="
                f"{os.path.join(self.browser_profile_dir, 'edge')}"
            )

            return webdriver.Edge(options=options)

        def make_firefox():
            options = FirefoxOptions()
            options.add_argument("--headless")

            return webdriver.Firefox(options=options)

        browsers = {
            "chrome": make_chrome,
            "edge": make_edge,
            "firefox": make_firefox
        }

        if browser:
            if browser not in browsers:
                raise RuntimeError(
                    "SELENIUM_BROWSER must be one of: "
                    "chrome, edge, firefox"
                )

            return browsers[browser]()

        last_error = None

        for make_browser in (
            make_chrome,
            make_edge,
            make_firefox
        ):
            try:
                return make_browser()

            except Exception as error:
                last_error = error

        raise RuntimeError(
            "Could not start Chrome, Edge, or Firefox "
            "for Selenium tests."
        ) from last_error