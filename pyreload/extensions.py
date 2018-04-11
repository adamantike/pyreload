# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
login_manager = LoginManager()
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
debug_toolbar = DebugToolbarExtension()
