from django.conf.urls import url

from barcode.views import api, docs

__author__ = 'rf9'

urlpatterns = [
    # URLs for the api
    url(r'^api/sources/$', api.source_list, name='sources'),
    url(r'^api/register/$', api.register, name='register'),
    url(r'^api/register/batch/$', api.register_batch, name='register_batch'),
    url(r'^api/barcodes/(\S+)/$', api.view_barcode, name='barcode'),
    url(r'^api/barcodes/$', api.view_barcodes, name='barcodes'),

    # URLs for the documentation
    url(r'^docs/$', docs.main, name='docs'),
]
