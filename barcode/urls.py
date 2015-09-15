from django.conf.urls import url
from barcode import views

__author__ = 'rf9'

urlpatterns = [
    url(r'^api/source/list/$', views.source_list, name='sources'),
    url(r'^api/register', views.register, name='register'),
]
