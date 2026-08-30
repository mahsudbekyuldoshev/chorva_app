from django.db.models.fields import CharField, IntegerField
from django.db.models.fields.files import ImageField

from .base import BaseModel


class Category(BaseModel):
    name_uz = CharField(max_length=255)
    name_ru = CharField(max_length=255)
    name_en = CharField(max_length=255)
    icon = ImageField(upload_to="categories/", null=True, blank=True)
    sort_order = IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name_uz
