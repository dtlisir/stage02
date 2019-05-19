# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import JsonResponse
from blueking.component.shortcuts import get_client_by_request
from home_application.models import CapacityData
from home_application.utils import get_job_instance_id, get_host_capaticy
# from home_application.celery_tasks import async_task, celery_chain_task


def home(request):
    """
    Home Page
    """
    # 执行异步任务查询磁盘数据入库
    # async_task.delay(request.user.username)

    # 执行定时任务查询磁盘数据入库
    # now = datetime.datetime.now()
    # async_task.apply_async(args=[request.user.username], eta=now + datetime.timedelta(seconds=5))

    # 串行任务执行
    # celery_chain_task(
    #     {
    #         'custom_func1': {'param1': 1},
    #         'custom_func2': {'param2': 2},
    #         'custom_func3': {'param3': 3}
    #     }
    # )
    return render(request, 'home_application/home.html')


# ------------------------------------
# 执行参数表单数据获取，业务、ip、作业
# ------------------------------------
def get_biz_list(request):
    """
    获取用户可访问的所有业务
    """
    biz_list = []
    client = get_client_by_request(request)
    kwargs = {
        'fields': ['bk_biz_id', 'bk_biz_name']
    }
    resp = client.cc.search_business(**kwargs)

    if resp.get('result'):
        data = resp.get('data', {}).get('info', {})
        for _d in data:
            biz_list.append({
                'name': _d.get('bk_biz_name'),
                'id': _d.get('bk_biz_id'),
            })

    result = {'result': resp.get('result'), 'data': biz_list}
    return JsonResponse(result)


def get_ip_by_bizid(request):
    """
    获取业务下IP
    """
    biz_id = int(request.GET.get('biz_id'))
    client = get_client_by_request(request)
    kwargs = {'bk_biz_id': biz_id,
              'condition': [
                  {
                      'bk_obj_id': 'biz',
                      'fields': ['bk_biz_id'],
                      'condition': [
                          {
                              'field': 'bk_biz_id',
                              'operator': '$eq',
                              'value': biz_id
                          }
                      ]
                  }
              ]
              }
    resp = client.cc.search_host(**kwargs)

    ip_list = []
    if resp.get('result'):
        data = resp.get('data', {}).get('info', {})
        for _d in data:
            _hostinfo = _d.get('host', {})
            if _hostinfo.get('bk_host_innerip') not in ip_list:
                ip_list.append(_hostinfo.get('bk_host_innerip'))

    ip_all = [{'ip': _ip} for _ip in ip_list]
    result = {'result': resp.get('result'), 'data': ip_all}
    return JsonResponse(result)


def get_joblist_by_bizid(request):
    """
    获取业务下的作业列表
    """
    biz_id = request.GET.get('biz_id')
    client = get_client_by_request(request)
    kwargs = {'bk_biz_id': biz_id}
    resp = client.job.get_job_list(**kwargs)
    job_list = []
    if resp.get('result'):
        data = resp.get('data', [])
        for _d in data:
            # 获取作业信息
            job_list.append({
                'job_id': _d.get('bk_job_id'),
                'job_name': _d.get('name'),
            })
    result = {'result': resp.get('result'), 'data': job_list}
    return JsonResponse(result)


def get_scriptlist_by_bizid(request):
    """
    获取业务下脚本列表
    """
    biz_id = request.GET.get('biz_id')
    client = get_client_by_request(request)
    kwargs = {'bk_biz_id': biz_id}
    resp = client.job.get_script_list(**kwargs)
    script_list = []
    if resp.get('result'):
        data = resp.get('data', {}).get('data', [])
        for _d in data:
            # 获取脚本信息
            script_list.append({
                'script_id': _d.get('id'),
                'script_name': _d.get('name'),
            })
    result = {'result': resp.get('result'), 'data': script_list}
    return JsonResponse(result)


# ------------------------------------
# 执行作业/脚本，获取实时磁盘容量数据
# ------------------------------------
def execute_job(request):
    """
    执行磁盘容量查询作业
    """
    biz_id = request.POST.get('biz_id')
    ip = request.POST.get('ip')
    job_id = request.POST.get('job_id', '')
    script_id = request.POST.get('script_id', '')

    # 调用作业平台API，或者作业执行实例ID
    client = get_client_by_request(request)
    result, job_instance_id = get_job_instance_id(client, biz_id, ip, job_id, script_id)

    result = {'result': result, 'data': job_instance_id}
    return JsonResponse(result)


def get_capacity(request):
    """
    获取作业执行结果，并解析执行结果展示
    """
    job_instance_id = request.GET.get('job_instance_id')
    biz_id = request.GET.get('biz_id')
    ip = request.GET.get('ip')
    # 调用作业平台API，或者作业执行详情，解析获取磁盘容量信息
    client = get_client_by_request(request)
    is_finish, capacity_data = get_host_capaticy(client, biz_id, job_instance_id, ip)

    return JsonResponse({'code': 0, 'message': 'success', 'data': capacity_data})


# ------------------------------------
# 获取视图数据
# ------------------------------------
def get_capacity_chartdata(request):
    """
    获取视图数据
    """
    ip = request.GET.get('ip')
    mounted = request.GET.get('mounted')
    capacitydatas = CapacityData.objects.filter(mounted=mounted, ip=ip)
    times = []
    data_dir = []
    for capacity in capacitydatas:
        times.append(capacity.createtime.strftime('%Y-%m-%d %H:%M:%S'))
        data_dir.append(capacity.use.strip('%'))

    result = {
        'code': 0,
        'result': True,
        'messge': 'success',
        'data': {
            'xAxis': times,
            'series': [
                {
                    'name': '%s: mounted: %s' % (ip, mounted),
                    'type': 'line',
                    'data': data_dir
                }
            ]
        }
    }
    return JsonResponse(result)
