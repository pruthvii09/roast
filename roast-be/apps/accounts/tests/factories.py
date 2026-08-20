import factory

from apps.accounts.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    display_name = factory.Faker("name")
    # Verified by default — most tests just want a normal working login;
    # OTP/verification-flow tests override this explicitly where the
    # unverified state is the thing under test.
    email_verified = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "Str0ngPassw0rd!")
        if create:
            self.save()
