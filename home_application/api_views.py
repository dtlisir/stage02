# -*- coding: utf-8 -*-

from django.http import JsonResponse
from blueapps.account.decorators import login_exempt
from home_application.models import CapacityData

TOKEN = '@adf*adsd^'


@login_exempt
def get_dfinfo_lisir(request):
    """
    获取磁盘容量数据 API
    """
    ip = request.GET.get('ip', '')
    # os = request.GET.get('os', '')
    mounted = request.GET.get('mounted', '')
    token = request.GET.get('token', '')
    if token != TOKEN:
        return JsonResponse({'result': False, 'data': [], 'message': "Token Authentication Failed"})

    capacitydatas = CapacityData.objects.all()
    if ip:
        capacitydatas = capacitydatas.filter(ip=ip)
    # if filesystem:
    #     capacitydatas = capacitydatas.filter(filesystem=filesystem)
    if mounted:
        capacitydatas = capacitydatas.filter(mounted=mounted)

    datalist = []
    for _data in capacitydatas:
        datalist.append(
            {
                'ip': _data.ip,
                # 'filesystem': _data.filesystem,
                'mounted': _data.mounted,
                'size': _data.size,
                'use': _data.use,
                'createtime': _data.createtime.strftime('%Y-%m-%d %H:%M:%S')
            }
        )

    return JsonResponse({'result': True, 'data': datalist, 'message': 'Success'})
