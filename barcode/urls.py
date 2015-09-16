from django.conf.urls import url
from barcode import views

__author__ = 'rf9'

urlpatterns = [
    url(r'^api/source/list/$', views.source_list, name='sources'),
    url(r'^api/register/$', views.register, name='register'),
    url(r'^api/barcode/(\S+)/$', views.view_barcode, name='barcode'),
    url(r'^api/uuid/(\S+)/$', views.view_uuid, name='uuid'),
    url(r'^docs/$', views.docs, name='docs'),
]
