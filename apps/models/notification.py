from django.db.models.deletion import CASCADE
from django.db.models.fields import BooleanField, CharField, TextField
from django.db.models.fields.related import ForeignKey

from .base import BaseModel
from .user import User


class Notification(BaseModel):
    TYPE_CHOICES = (
        ("message", "Message"),
        ("follow", "Follow"),
        ("favorite", "Favorite"),
        ("listing_approved", "Listing Approved"),
        ("listing_rejected", "Listing Rejected"),
        ("system", "System"),
    )
    user = ForeignKey(User, CASCADE, related_name="notifications")
    type = CharField(max_length=20, choices=TYPE_CHOICES)
    title = CharField(max_length=255)
    body = TextField()
    is_read = BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
