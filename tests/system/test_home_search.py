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