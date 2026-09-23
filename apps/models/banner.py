from django.db.models import (
    CASCADE,
    CharField,
    ForeignKey,
    ImageField,
    PositiveIntegerField,
    URLField,
)

from apps.models.base import BaseModel
from apps.models.category import Category


class Banner(BaseModel):
    LINK_TYPE_CHOICES = (
        ("none", "Havolasiz"),
        ("category", "Kategoriya"),
        ("url", "Tashqi havola"),
        ("product", "E'lon"),
    )

    image = ImageField(upload_to="banners/")
    link_type = CharField(max_length=20, choices=LINK_TYPE_CHOICES, default="none")
    link_url = URLField(blank=True, null=True)
    category = ForeignKey(
        Category, on_delete=CASCADE, null=True, blank=True, related_name="banners"
    )
    view_count = PositiveIntegerField(default=0)
    sort_order = PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"Banner ({self.link_type})"
