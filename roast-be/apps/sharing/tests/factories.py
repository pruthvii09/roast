import factory

from apps.roasts.tests.factories import RoastRunFactory

from ..models import Reaction, ReactionType, ShareLink


class ShareLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShareLink

    roast = factory.SubFactory(RoastRunFactory)
    owner = factory.SelfAttribute("roast.owner")


class ReactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Reaction

    share_link = factory.SubFactory(ShareLinkFactory)
    reaction_type = ReactionType.FIRE
    count = 1
