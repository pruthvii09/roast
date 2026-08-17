import secrets

from django.db import models

from apps.common.models import TimeStampedUUIDModel


def generate_share_token() -> str:
    return secrets.token_urlsafe(32)


class ShareLink(TimeStampedUUIDModel):
    """
    A public, revocable link exposing one specific RoastRun's output to
    anonymous visitors. Points at a RoastRun (not its Submission) — a
    link shares one exact roast attempt (language/intensity/content),
    never "whatever this submission's current roast happens to be".

    `token` is a separate opaque, URL-safe value from the roast's own
    UUID `id` — generated independently so a link can be revoked/rotated
    without the RoastRun's id ever appearing in a public URL.

    Soft-revoked, not deleted: `revoked_at` turns off public access
    while keeping the row (and its view_count/reaction history) around.
    The partial unique constraint below allows at most one *active*
    (revoked_at IS NULL) link per roast at a time — re-sharing after a
    revoke creates a new row with a new token rather than reactivating
    the old one, mirroring RoastRun's own in-flight partial unique
    constraint pattern (apps.roasts.models.RoastRun).

    `owner` is a denormalized copy of `roast.owner`, same rationale as
    RoastRun.owner itself — cheap "links I created" queries with no
    join. Permission checks go through `roast.owner_id`, not this field
    (see apps.sharing.permissions.IsShareLinkOwner).
    """

    roast = models.ForeignKey(
        "roasts.RoastRun", on_delete=models.CASCADE, related_name="share_links"
    )
    owner = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="share_links")
    token = models.CharField(
        max_length=64, unique=True, default=generate_share_token, editable=False
    )
    view_count = models.PositiveIntegerField(default=0)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "sharing_sharelink"
        indexes = [
            models.Index(fields=["roast", "created_at"], name="sharelink_roast_created_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["roast"],
                condition=models.Q(revoked_at__isnull=True),
                name="unique_active_share_link_per_roast",
            ),
        ]

    def __str__(self):
        return f"ShareLink({self.roast_id}, active={self.revoked_at is None})"


class ReactionType(models.TextChoices):
    FIRE = "fire", "Brutal"
    SKULL = "skull", "Deceased"
    LAUGHING = "laughing", "Painfully funny"
    CLAP = "clap", "Fair"


class Reaction(TimeStampedUUIDModel):
    """
    An aggregate counter per (share_link, reaction_type) — NOT a
    per-visitor row. Anonymous, unauthenticated visitors have no
    reliable identity to dedupe reactions against without IP tracking
    (which would be PII this app otherwise avoids collecting), so this
    table doesn't try: any client-side "you already reacted" affordance
    on the frontend is a UX nicety only, never a security boundary, and
    the same visitor reacting twice simply increments `count` again.
    """

    share_link = models.ForeignKey(ShareLink, on_delete=models.CASCADE, related_name="reactions")
    reaction_type = models.CharField(max_length=20, choices=ReactionType.choices)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "sharing_reaction"
        constraints = [
            models.UniqueConstraint(
                fields=["share_link", "reaction_type"], name="unique_reaction_type_per_share_link"
            ),
        ]

    def __str__(self):
        return f"{self.reaction_type}:{self.count} ({self.share_link_id})"
