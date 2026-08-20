import pytest
from django.utils import timezone

from apps.roasts.models import RoastStatus
from apps.roasts.tests.factories import RoastRunFactory
from apps.submissions.models import SubmissionVisibility
from apps.submissions.tests.factories import SubmissionFactory

from ..models import ReactionType
from ..selectors import get_wall_of_fame_roasts
from .factories import ReactionFactory, ShareLinkFactory

pytestmark = pytest.mark.django_db


def _public_link(**roast_kwargs):
    submission = SubmissionFactory(visibility=SubmissionVisibility.PUBLIC)
    roast = RoastRunFactory(submission=submission, status=RoastStatus.COMPLETED, **roast_kwargs)
    return ShareLinkFactory(roast=roast)


class TestGetWallOfFameRoasts:
    def test_includes_public_completed_active_links(self):
        link = _public_link()
        results = list(get_wall_of_fame_roasts())
        assert results == [link]

    def test_excludes_private_visibility(self):
        submission = SubmissionFactory(visibility=SubmissionVisibility.PRIVATE)
        roast = RoastRunFactory(submission=submission, status=RoastStatus.COMPLETED)
        ShareLinkFactory(roast=roast)
        assert list(get_wall_of_fame_roasts()) == []

    def test_excludes_link_only_visibility(self):
        submission = SubmissionFactory(visibility=SubmissionVisibility.LINK)
        roast = RoastRunFactory(submission=submission, status=RoastStatus.COMPLETED)
        ShareLinkFactory(roast=roast)
        assert list(get_wall_of_fame_roasts()) == []

    def test_excludes_revoked_links(self):
        link = _public_link()
        link.revoked_at = timezone.now()
        link.save(update_fields=["revoked_at"])
        assert list(get_wall_of_fame_roasts()) == []

    def test_excludes_non_completed_roasts(self):
        submission = SubmissionFactory(visibility=SubmissionVisibility.PUBLIC)
        roast = RoastRunFactory(submission=submission, status=RoastStatus.PROCESSING)
        ShareLinkFactory(roast=roast)
        assert list(get_wall_of_fame_roasts()) == []

    def test_excludes_soft_deleted_submissions(self):
        link = _public_link()
        link.roast.submission.soft_delete()
        assert list(get_wall_of_fame_roasts()) == []

    def test_default_ordering_ranks_by_total_reactions(self):
        low = _public_link()
        high = _public_link()
        ReactionFactory(share_link=high, reaction_type=ReactionType.FIRE, count=5)
        ReactionFactory(share_link=low, reaction_type=ReactionType.FIRE, count=1)

        results = list(get_wall_of_fame_roasts())

        assert results == [high, low]
        assert results[0].total_reactions == 5
        assert results[1].total_reactions == 1

    def test_ordering_new_ranks_by_recency(self):
        older = _public_link()
        newer = _public_link()

        results = list(get_wall_of_fame_roasts(ordering="new"))

        assert results == [newer, older]


class TestWallOfFameListView:
    def test_returns_paginated_public_entries(self, api_client):
        link = _public_link()

        response = api_client.get("/api/v1/share/wall-of-fame/")

        assert response.status_code == 200
        body = response.json()
        assert body["meta"]["count"] == 1
        entry = body["data"][0]
        assert entry["token"] == link.token
        assert entry["score"] == link.roast.score
        assert entry["summary"] == link.roast.summary
        assert entry["total_reactions"] == 0

    def test_never_leaks_owner_or_id(self, api_client):
        _public_link()

        response = api_client.get("/api/v1/share/wall-of-fame/")

        entry = response.json()["data"][0]
        assert "id" not in entry
        assert "owner" not in entry
        assert set(entry["submission"]) == {"submission_type", "title"}

    def test_excludes_private_roasts(self, api_client):
        submission = SubmissionFactory(visibility=SubmissionVisibility.PRIVATE)
        roast = RoastRunFactory(submission=submission, status=RoastStatus.COMPLETED)
        ShareLinkFactory(roast=roast)

        response = api_client.get("/api/v1/share/wall-of-fame/")

        assert response.json()["data"] == []

    def test_no_authorization_header_required(self, api_client):
        _public_link()
        response = api_client.get("/api/v1/share/wall-of-fame/")
        assert response.status_code == 200
