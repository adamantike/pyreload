# -*- coding: utf-8 -*-
"""Model unit tests for user app."""
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import pytest

from pyreload.user.models import User
from tests.factories.user import UserFactory


@pytest.mark.usefixtures('db')
class TestUser:
    """User tests."""

    def test_get_by_id(self):
        """Get user by ID."""
        user = User('foo', 'foo@bar.com')
        user.save()

        retrieved = User.get_by_id(user.id)
        assert retrieved == user

    def test_password_is_nullable(self):
        """Test null password."""
        user = User(username='foo', email='foo@bar.com')
        user.save()
        assert user.password is None

    def test_factory(self, db):
        """Test user factory."""
        user = UserFactory(password='myprecious')
        db.session.commit()
        assert bool(user.username)
        assert bool(user.email)
        assert user.check_password('myprecious')

    def test_check_password(self):
        """Check password."""
        user = User.create(
            username='foo',
            email='foo@bar.com',
            password='foobarbaz123',
        )
        assert user.check_password('foobarbaz123') is True
        assert user.check_password('barfoobaz') is False
