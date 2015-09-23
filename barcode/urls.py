from django.conf.urls import url

from barcode.views import api, docs

__author__ = 'rf9'

urlpatterns = [
    # URLs for the api
    url(r'^api/sources/$', api.SourcesView.as_view(), name='sources'),
    url(r'^api/register/$', api.register, name='register'),
    url(r'^api/register/batch/$', api.register_batch, name='register_batch'),
    url(r'^api/barcodes/(?P<barcode>\S+)/$', api.BarcodeView.as_view(), name='barcode'),
    url(r'^api/barcodes/$', api.BarcodesView.as_view(), name='barcodes'),

    # URLs for the documentation
    url(r'^docs/$', docs.main, name='docs'),
]
