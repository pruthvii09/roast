from django.db import migrations


def mark_existing_users_verified(apps, schema_editor):
    """
    Grandfathers in every account created before OTP verification
    existed — they registered under the old rules and were never sent a
    code, so gating their login on email_verified now would lock every
    pre-existing account out with no way back in short of an admin/DB fix.
    Only new registrations from here on start with email_verified=False.
    """
    User = apps.get_model("accounts", "User")
    User.objects.filter(email_verified=False).update(email_verified=True)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_user_email_verified_emailotp"),
    ]

    operations = [
        migrations.RunPython(mark_existing_users_verified, migrations.RunPython.noop),
    ]
