from django.db import models
import uuid as uuid

MAX_LENGTH = 128


class Barcode(models.Model):
    barcode = models.CharField(max_length=MAX_LENGTH, unique=True)
    source = models.ForeignKey('Source')
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)


class Source(models.Model):
    name = models.CharField(max_length=10)


class NumberGenerator(models.Model):
    pass
