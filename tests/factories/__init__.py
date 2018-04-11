# -*- coding: utf-8 -*-
"""Factories to help in tests."""
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from factory.alchemy import SQLAlchemyModelFactory

from pyreload.database import db


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory."""

    class Meta:
        """Factory configuration."""

        abstract = True
        sqlalchemy_session = db.session
