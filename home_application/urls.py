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
    # 表单下拉数据获取及渲染
    url(r'^get_biz_list/$', views.get_biz_list),
    url(r'^get_ip_by_bizid/$', views.get_ip_by_bizid),
    url(r'^get_job_list/$', views.get_joblist_by_bizid),
    url(r'^get_script_list/$', views.get_scriptlist_by_bizid),
    # 执行作业/脚本，获取容量数据
    url(r'^execute_job/$', views.execute_job),
    url(r'^get_capacity/$', views.get_capacity),
    # 获取视图数据
    url(r'^chartdata/$', views.get_capacity_chartdata),
)
