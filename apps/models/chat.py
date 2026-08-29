from django.db import models
from django.db.models.constraints import CheckConstraint
from django.db.models.deletion import CASCADE, SET_NULL
from django.db.models.expressions import F
from django.db.models.fields import BooleanField, TextField
from django.db.models.fields.related import ForeignKey
from django.db.models.query_utils import Q

from .base import BaseModel
from .listing import Listing
from .user import User


class Conversation(BaseModel):
    buyer = ForeignKey(User, CASCADE, related_name="buying_conversations")
    seller = ForeignKey(User, CASCADE, related_name="selling_conversations")
    listing = ForeignKey(
        Listing, SET_NULL, null=True, blank=True, related_name="conversations"
    )

    class Meta:
        unique_together = ("buyer", "seller", "listing")
        constraints = [
            CheckConstraint(
                condition=~Q(buyer=F("seller")), name="buyer_cannot_be_seller"
            )
        ]


class Message(BaseModel):
    conversation = ForeignKey(Conversation, CASCADE, related_name="messages")
    sender = ForeignKey(User, CASCADE, related_name="sent_messages")
    text = TextField()
    is_read = BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
