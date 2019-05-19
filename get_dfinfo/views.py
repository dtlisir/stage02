# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import JsonResponse
from blueking.component.shortcuts import get_client_by_request


def home(request):
    """
    Home Page
    """

    return render(request, 'get_dfinfo/home.html')


def get_dfinfo(request):
    ip = request.GET.get('ip')
    # os = request.GET.get('os')
    mounted = request.GET.get('mounted')

    # 调用自己开发的API组件
    client = get_client_by_request(request)
    kwargs = {
        'ip': ip,
        'mounted': mounted,
        'token': '@adf*adsd^',
    }
    resp = client.dim.get_dfinfo(**kwargs)
    return JsonResponse({'result': resp['result'], 'data': resp['data'], 'message': resp['message']})
