# -*- coding: utf-8 -*-
"""testapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url

from home_application import views

urlpatterns = (
    url(r'^$', views.home),
    url(r'^get_biz_list/$', views.get_biz_list),
    url(r'^get_ip_by_bizid/$', views.get_ip_by_bizid),
    url(r'^get_job_list/$', views.get_joblist_by_bizid),
    url(r'^get_script_list/$', views.get_scriptlist_by_bizid),
    url(r'^execute_script/$', views.execute_script),
    url(r'^get_operations/$', views.get_operations),
    url(r'^get_log/(?P<operation_id>\d+)/$', views.get_log),
    url(r'^disk_chartdata/$', views.get_disk_chartdata),
    url(r'^mem_chartdata/$', views.get_mem_chartdata),
)
