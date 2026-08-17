import factory

from apps.submissions.tests.factories import SubmissionFactory

from ..models import (
    RoastFinding,
    RoastIntensity,
    RoastLanguage,
    RoastRun,
    RoastSection,
    RoastSeverity,
    RoastStatus,
)


class RoastRunFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RoastRun

    submission = factory.SubFactory(SubmissionFactory)
    owner = factory.SelfAttribute("submission.owner")
    language = RoastLanguage.EN
    intensity = RoastIntensity.SARCASTIC
    status = RoastStatus.COMPLETED
    engine_version = "v1"
    summary = factory.Faker("sentence")
    final_verdict = factory.Faker("sentence")
    score = 42


class RoastSectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RoastSection

    roast = factory.SubFactory(RoastRunFactory)
    key = factory.Sequence(lambda n: f"section-{n}")
    title = factory.Faker("sentence", nb_words=3)
    content = factory.Faker("paragraph")
    position = factory.Sequence(lambda n: n)


class RoastFindingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RoastFinding

    roast = factory.SubFactory(RoastRunFactory)
    category = "general"
    severity = RoastSeverity.MEDIUM
    title = factory.Faker("sentence", nb_words=3)
    roast_text = factory.Faker("sentence")
    actual_feedback = factory.Faker("sentence")
    position = factory.Sequence(lambda n: n)
