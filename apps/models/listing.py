from django.db.models.deletion import CASCADE, SET_NULL
from django.db.models.fields import (
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    FloatField,
    IntegerField,
    TextField,
)
from django.db.models.fields.files import FileField, ImageField
from django.db.models.fields.related import ForeignKey

from .base import BaseModel
from .category import Category
from .user import User


class Listing(BaseModel):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("active", "Active"),
        ("sold", "Sold"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    )
    TYPE_CHOICES = (
        ("normal", "Normal"),
        ("top", "Top"),
        ("vip", "Vip"),
    )

    user = ForeignKey(User, CASCADE, related_name="listings")
    category = ForeignKey(Category, CASCADE, related_name="listings")
    title = CharField(max_length=255)
    description = TextField()
    price = DecimalField(max_digits=12, decimal_places=2)
    currency = CharField(max_length=3, default="UZS")
    status = CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    listing_type = CharField(max_length=10, choices=TYPE_CHOICES, default="normal")
    # TODO: PostGIS PointField'ga o'tish kerak — GDAL/GEOS/PROJ kutubxonalari o'rnatilgandan keyin (Ubuntu: apt install gdal-bin libgdal-dev libgeos-dev libproj-dev; keyin py'da location = gis_PointField(geography=True, srid=4326) ga qaytariladi va migration generate qilinadi).
    # Hozircha listings/map/ endpoint'ida radius bo'yicha filtrlashni oddiy Haversine formula (SQL yoki Python darajasida) bilan vaqtincha amalga oshiring, keyin PostGIS o'rnatilganda distance_lte ga almashtiriladi.
    lat = FloatField()
    lng = FloatField()
    address_text = CharField(max_length=255)
    view_count = IntegerField(default=0)
    expires_at = DateTimeField()

    def __str__(self):
        return self.title


class ListingMedia(BaseModel):
    MEDIA_TYPE_CHOICES = (
        ("image", "Image"),
        ("video", "Video"),
    )
    listing = ForeignKey(Listing, CASCADE, related_name="media")
    media_type = CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    file = FileField(upload_to="listings/")
    thumbnail = ImageField(upload_to="thumbnails/", null=True, blank=True)
    sort_order = IntegerField(default=0)


class Favorite(BaseModel):
    user = ForeignKey(User, CASCADE, related_name="favorites")
    listing = ForeignKey(Listing, CASCADE, related_name="favorites")

    class Meta:
        unique_together = ("user", "listing")


class Reel(BaseModel):
    user = ForeignKey(User, CASCADE, related_name="reels")
    listing = ForeignKey(Listing, SET_NULL, null=True, blank=True, related_name="reels")
    video = FileField(upload_to="reels/")
    caption = TextField(blank=True)
    view_count = IntegerField(default=0)


class Report(BaseModel):
    REASON_CHOICES = (
        ("spam", "Spam"),
        ("fraud", "Fraud"),
        ("inappropriate", "Inappropriate"),
        ("sold_elsewhere", "Sold elsewhere"),
        ("other", "Other"),
    )
    reporter = ForeignKey(User, CASCADE, related_name="reports")
    target_user = ForeignKey(User, CASCADE, null=True, blank=True)
    target_listing = ForeignKey(Listing, CASCADE, null=True, blank=True)
    reason = CharField(max_length=20, choices=REASON_CHOICES)
    comment = TextField(blank=True)
    is_resolved = BooleanField(default=False)
