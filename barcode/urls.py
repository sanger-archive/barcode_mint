from django.conf.urls import url

from barcode.views import api, docs

__author__ = 'rf9'

urlpatterns = [
    # URLs for the api
    url(r'^api/source/list/$', api.source_list, name='sources'),
    url(r'^api/register/$', api.register, name='register'),
    url(r'^api/barcode/(\S+)/$', api.view_barcode, name='barcode'),
    url(r'^api/uuid/(\S+)/$', api.view_uuid, name='uuid'),

    # URLs for the documentation
    url(r'^docs/$', docs.main, name='docs'),
]
