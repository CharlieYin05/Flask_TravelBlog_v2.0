import os
import shutil
import tempfile
import unittest
from pathlib import Path

from flask import Flask

from app.extensions import csrf, db, login
from app.forms import LogoutForm
from app.models import User
from app.routes import main_bp

class HomeSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        project_root = Path(__file__).resolve().parents[2]

        self.app = Flask(
            __name__,
            template_folder=str(project_root / "app" / "templates"),
            static_folder=str(project_root / "app" / "static"),
        )
