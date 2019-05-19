# -*- coding: utf-8 -*-

from django.conf.urls import url
from home_application import api_views


urlpatterns = (
    url(r'^get_dfinfo_lisir/$', api_views.get_dfinfo_lisir),
)