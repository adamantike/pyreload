# -*- coding: utf-8 -*-
"""Factories to help in tests."""
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from factory import (
    PostGenerationMethodCall,
    Sequence,
)
from factory.alchemy import SQLAlchemyModelFactory

from pyreload.database import db
from pyreload.user.models import User


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory."""

    class Meta:
        """Factory configuration."""

        abstract = True
        sqlalchemy_session = db.session


class UserFactory(BaseFactory):
    """User factory."""

    username = Sequence(lambda n: 'user{0}'.format(n))
    email = Sequence(lambda n: 'user{0}@example.com'.format(n))
    password = PostGenerationMethodCall('set_password', 'example')

    class Meta:
        """Factory configuration."""

        model = User
