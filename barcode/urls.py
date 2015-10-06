from django.conf.urls import url
from rest_framework import routers

from barcode.views import api, docs

__author__ = 'rf9'

router = routers.SimpleRouter(trailing_slash=False)
router.register(r'api/barcodes', api.BarcodeViewSet, base_name='barcode')
router.register(r'api/sources', api.SourcesViewSet)

urlpatterns = [
    # URLs for the documentation
    url(r'^docs/$', docs.main, name='docs'),
] + router.urls

