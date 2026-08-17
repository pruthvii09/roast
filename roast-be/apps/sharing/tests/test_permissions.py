import pytest

from apps.accounts.tests.factories import UserFactory
from apps.sharing.permissions import IsShareLinkOwner
from apps.sharing.tests.factories import ShareLinkFactory

pytestmark = pytest.mark.django_db


class _DummyRequest:
    def __init__(self, user):
        self.user = user


def test_owner_has_permission():
    link = ShareLinkFactory()
    assert IsShareLinkOwner().has_object_permission(_DummyRequest(link.owner), None, link) is True


def test_non_owner_denied():
    link = ShareLinkFactory()
    other = UserFactory()
    assert IsShareLinkOwner().has_object_permission(_DummyRequest(other), None, link) is False
