import pytest

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_create_user_normalizes_email():
    user = User.objects.create_user(email="Foo@Example.COM", password="Str0ngPassw0rd!")
    assert user.email == "Foo@example.com"


def test_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="Str0ngPassw0rd!")


def test_create_user_hashes_password():
    user = User.objects.create_user(email="foo@example.com", password="Str0ngPassw0rd!")
    assert user.password != "Str0ngPassw0rd!"
    assert user.check_password("Str0ngPassw0rd!")


def test_create_superuser_sets_flags():
    user = User.objects.create_superuser(email="admin@example.com", password="Str0ngPassw0rd!")
    assert user.is_staff is True
    assert user.is_superuser is True
