# -*- coding: utf-8 -*-
"""User models."""
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from flask_login import UserMixin

from pyreload.database import (
    Column,
    Model,
    SurrogatePK,
    db,
)
from pyreload.extensions import bcrypt


class User(UserMixin, SurrogatePK, Model):
    """A user of the app."""

    __tablename__ = 'users'

    username = Column('name', db.String(80), unique=True, nullable=False)
    email = Column(db.String(120), unique=True, nullable=False)
    # The hashed password
    password = Column(db.Binary(128), nullable=True)
    permissions = Column('permission', db.Integer, nullable=False, default=0)
    role = Column(db.SmallInteger, nullable=False, default=0)
    template = Column(db.String(255))

    def __init__(self, username, email, password=None, **kwargs):
        """Create instance."""
        db.Model.__init__(self, username=username, email=email, **kwargs)
        if password:
            self.set_password(password)
        else:
            self.password = None

    def set_password(self, password):
        """Set password."""
        self.password = bcrypt.generate_password_hash(password)

    def check_password(self, value):
        """Check password."""
        return bcrypt.check_password_hash(self.password, value)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<User({username!r})>'.format(username=self.username)
