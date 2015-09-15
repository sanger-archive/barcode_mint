from django.contrib import admin

from barcode.models import Source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    fields = ['name']
    list_display = ['name']
