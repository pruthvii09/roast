import factory

from apps.accounts.tests.factories import UserFactory
from apps.submissions.models import Submission, SubmissionType


class SubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Submission

    owner = factory.SubFactory(UserFactory)
    submission_type = SubmissionType.WEBSITE
    source_url = "https://example.com/portfolio"
    title = factory.Faker("sentence", nb_words=3)
