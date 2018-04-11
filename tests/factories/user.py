# -*- coding: utf-8 -*-
"""Factories for the user app."""
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

from pyreload.user.models import User
from tests.factories import BaseFactory


class UserFactory(BaseFactory):
    """User factory."""

    username = Sequence(lambda n: 'user{0}'.format(n))
    email = Sequence(lambda n: 'user{0}@example.com'.format(n))
    password = PostGenerationMethodCall('set_password', 'example')

    class Meta:
        """Factory configuration."""

        model = User
