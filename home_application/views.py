# -*- coding: utf-8 -*-

import os
import time
import base64
import datetime
import json
from django.utils import timezone
from django.shortcuts import render
from django.http import JsonResponse
from config import APP_CODE, SECRET_KEY
from blueking.component.shortcuts import get_client_by_request, get_client_by_user
from home_application.models import Operation
from celery.task import task
from celery.schedules import crontab
from celery.task import periodic_task
from blueapps.utils.logger import logger


def home(request):
    """
    首页
    """
    # client = get_client_by_request(request)
    # kwargs = {'token': '@adf*adsd^'}
    # resp = client.cm.get_capacity(**kwargs)

    return render(request, 'home_application/home.html')


# ------------------------------------
# 执行参数表单数据获取，业务、ip、作业
# ------------------------------------
def get_biz_list(request):
    """
    获取所有业务
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


def execute_job(request):
    """
    执行作业
    """
    biz_id = request.POST.get("biz_id")
    biz_name = request.POST.get("biz_name")
    job_id = request.POST.get("job_id")
    job_name = request.POST.get("job_name")
    ip = request.POST.get("ip")

    if biz_id:
        biz_id = int(biz_id)

    if job_id:
        job_id = int(job_id)

    client = get_client_by_request(request)
    execute_task = run_job.delay(client, biz_id, job_id, ip)

    op_db = Operation.objects.create(
        biz=biz_name,
        task=job_name,
        ip=ip,
        celery_id=execute_task.id,
        user=request.user.username
    )

    return JsonResponse({"result": True, "data": op_db.celery_id, "message": "success"})


@task()
def run_job(client, biz_id, job_id, ip):
    """执行作业"""

    # 执行中
    op_db = Operation.objects.filter(celery_id=run_script.request.id).update(
        status="running"
    )
    resp = client.job.get_job_detail(
        bk_biz_id=biz_id,
        bk_job_id=job_id
    )

    steps_args = []
    if resp.get('result'):
        data = resp.get('data', {})
        steps = data.get('steps', [])
        # 组装步骤参数
        for _step in steps:
            steps_args.append(
                {
                    'step_id': int(_step.get('step_id')),
                    'ip_list': [{
                        'bk_cloud_id': 0,
                        'ip': ip,
                    }],
                }
            )

    resp = client.job.execute_job(
        bk_biz_id=biz_id,
        bk_job_id=job_id,
        steps=steps_args
    )
    # 启动失败
    if not resp.get('result', False):
        op_db = Operation.objects.filter(celery_id=run_script.request.id).update(
            log=json.dumps(resp.get("message")),
            end_time=timezone.now(),
            result=False,
            status="start_failed"
        )
    task_id = resp.get('data').get('job_instance_id')
    poll_job_task(client, biz_id, task_id)

    # 查询日志
    resp = client.job.get_job_instance_log(job_instance_id=task_id, bk_biz_id=biz_id)
    log = resp['data'][0]['step_results'][0]['ip_logs'][0]['log_content']
    status = resp['data'][0]['status']
    result = True if status == 3 else False
    now = datetime.datetime.now()
    logger.info("celery任务调用成功，当前时间：{}".format(now))
    op_db = Operation.objects.filter(celery_id=run_script.request.id).update(
        log=log,
        end_time=timezone.now(),
        result=result,
        status="successed" if result else "failed"
    )


def execute_script(request):
    """
    执行脚本
    """
    biz_id = request.POST.get("biz_id")
    biz_name = request.POST.get("biz_name")
    script_id = request.POST.get("script_id")
    script_name = request.POST.get("script_name")
    ip = request.POST.get("ip")

    if biz_id:
        biz_id = int(biz_id)

    if script_id:
        script_id = int(script_id)

    client = get_client_by_request(request)
    execute_task = run_script.delay(client, biz_id, script_id, ip)

    op_db = Operation.objects.create(
        biz=biz_name,
        task=script_name,
        ip=ip,
        celery_id=execute_task.id,
        user=request.user.username
    )

    return JsonResponse({"result": True, "data": op_db.celery_id, "message": "success"})


@task()
def run_script(client, biz_id, script_id, ip):
    """快速执行脚本"""

    # 执行中
    op_db = Operation.objects.filter(celery_id=run_script.request.id).update(
        status="running"
    )

    resp = client.job.fast_execute_script(
        bk_biz_id=biz_id,
        account="root",
        script_id=script_id,
        ip_list=[{"bk_cloud_id": 0, "ip": ip}]
    )
    # 启动失败
    if not resp.get('result', False):
        op_db = Operation.objects.filter(celery_id=run_script.request.id).update(
            log=json.dumps(resp.get("message")),
            end_time=timezone.now(),
            result=False,
            status="start_failed"
        )
    task_id = resp.get('data').get('job_instance_id')
    poll_job_task(client, biz_id, task_id)

    # 查询日志
    resp = client.job.get_job_instance_log(job_instance_id=task_id, bk_biz_id=biz_id)
    log = resp['data'][0]['step_results'][0]['ip_logs'][0]['log_content']
    status = resp['data'][0]['status']
    result = True if status == 3 else False
    now = datetime.datetime.now()
    logger.info("celery任务调用成功，当前时间：{}".format(now))
    op_db = Operation.objects.filter(celery_id=run_script.request.id).update(
        log=log,
        end_time=timezone.now(),
        result=result,
        status="successed" if result else "failed"
    )


def poll_job_task(client, biz_id, job_instance_id):
    """true/false/timeout"""

    count = 0

    res = client.job.get_job_instance_status(job_instance_id=job_instance_id, bk_biz_id=biz_id)

    while not res.get('data', {}).get('is_finished') and count < 30:
        res = client.job.get_job_instance_status(job_instance_id=job_instance_id, bk_biz_id=biz_id)
        count += 1
        time.sleep(3)

    return res


def get_operations(request):
    """
    Ajax加载操作记录
    """
    operations = Operation.objects.all()
    data = [opt.to_dict() for opt in operations]
    return JsonResponse({
        'result': True,
        'data': data,
        'message': "success"
    })


def get_log(request, operation_id):
    """查询日志"""

    operation = Operation.objects.get(id=operation_id)
    job_log_content = operation.log
    log_content = '<div class="log-content">'
    log_content += ''.join(
            map(lambda x: '<prev>{}</prev><br>'.format(x), job_log_content.split('\n'))
        )
    log_content += '</div>'

    return JsonResponse({
        'result': True,
        'data': log_content
    })


@periodic_task(run_every=crontab(minute='0', hour='*/1', day_of_week="*"))
def disk_execute_script(user="80167885"):
    try:
        op_db = Operation.objects.create(
            biz="业务1",
            task="磁盘分区使用率",
            ip="10.0.1.192",
            celery_id=disk_execute_script.request.id,
            user=user,
            status="running"
        )
        client = get_client_by_user(user)
        result = client.job.fast_execute_script(
            bk_app_code=APP_CODE,
            bk_app_secret=SECRET_KEY,
            bk_username=user,
            bk_biz_id=3,
            script_id=33,
            ip_list=[{"bk_cloud_id": 0, "ip": "10.0.1.192"}],
            script_type=1,
            account='root'
        )
        if result["result"]:
            script_result = get_job_instance_log(client, result["data"]["job_instance_id"], user)
            if script_result['result']:
                data = script_result['log'].split('\n')
                logger.info("[10.0.1.192]根分区磁盘使用率为：{}".format(data[1]))
                op_db = Operation.objects.filter(celery_id=disk_execute_script.request.id).update(
                    log=script_result['log'],
                    end_time=timezone.now(),
                    result=True,
                    status="successed" if result else "failed"
                )
            else:
                op_db = Operation.objects.filter(celery_id=disk_execute_script.request.id).update(
                    log=json.dumps([result.get("message")]),
                    end_time=timezone.now(),
                    result=False,
                    status="start_failed"
                )
        else:
            op_db = Operation.objects.filter(celery_id=disk_execute_script.request.id).update(
                log=json.dumps([result.get("message")]),
                end_time=timezone.now(),
                result=False,
                status="start_failed"
            )
    except Exception as e:
        return logger.error("fast_execute_script失败，原因是：%s" % (str(e)))
    now = datetime.datetime.now()
    logger.info("celery周期任务调用成功，当前时间：{}".format(now))


@periodic_task(run_every=crontab(minute='*/30', hour='*', day_of_week="*"))
def mem_execute_script(user="80167885"):
    try:
        op_db = Operation.objects.create(
            biz="业务1",
            task="内存使用率",
            ip="10.0.1.192",
            celery_id=mem_execute_script.request.id,
            user=user,
            status="running"
        )
        client = get_client_by_user(user)
        result = client.job.fast_execute_script(
            bk_app_code=APP_CODE,
            bk_app_secret=SECRET_KEY,
            bk_username=user,
            bk_biz_id=3,
            script_id=35,
            ip_list=[{"bk_cloud_id": 0, "ip": "10.0.1.192"}],
            script_type=1,
            account='root'
        )
        if result["result"]:
            script_result = get_job_instance_log(client, result["data"]["job_instance_id"], user)
            if script_result['result']:
                data = script_result['log'].split('\n')
                logger.info("[10.0.1.192]内存使用率为：{}".format(data[1]))
                op_db = Operation.objects.filter(celery_id=mem_execute_script.request.id).update(
                    log=script_result['log'],
                    end_time=timezone.now(),
                    result=True,
                    status="successed" if result else "failed"
                )
            else:
                pass
                op_db = Operation.objects.filter(celery_id=mem_execute_script.request.id).update(
                    log=json.dumps([result.get("message")]),
                    end_time=timezone.now(),
                    result=False,
                    status="start_failed"
                )
        else:
            pass
            op_db = Operation.objects.filter(celery_id=mem_execute_script.request.id).update(
                log=json.dumps([result.get("message")]),
                end_time=timezone.now(),
                result=False,
                status="start_failed"
            )
    except Exception as e:
        return logger.error("mem_execute_script失败，原因是：%s" % (str(e)))
    now = datetime.datetime.now()
    logger.info("celery周期任务调用成功，当前时间：{}".format(now))


def get_job_instance_log(client, job_instance_id, user):
    kwargs = {
        "bk_app_code": APP_CODE,
        "bk_app_secret": SECRET_KEY,
        "bk_username": user,
        "bk_biz_id": 3,
        "job_instance_id": job_instance_id
    }
    result = client.job.get_job_instance_log(**kwargs)
    if result["result"]:
        if result["data"][0]["is_finished"]:
            if result['data'][0]['status'] == 3:
                log = result['data'][0]['step_results'][0]['ip_logs'][0]['log_content']
                status = result['data'][0]['status']
                return {'result': True, 'log': log, 'status': status}
            else:
                return {'result': False}
        else:
            time.sleep(3)
            return get_job_instance_log(client, job_instance_id, user)
    else:
        return {'result': False}


def get_disk_chartdata(request):
    """
    获取磁盘数据
    """
    ip = request.GET.get('ip')
    task_name = request.GET.get('task_name')
    capacitydatas = Operation.objects.filter(task=task_name, ip=ip, result=True)
    times = []
    data_dir = []
    for capacity in capacitydatas:
        times.append(capacity.start_time.strftime('%Y-%m-%d %H:%M:%S'))
        data = capacity.log.split('\n')
        data_dir.append(data[1].strip('%'))

    result = {
        'code': 0,
        'result': True,
        'messge': 'success',
        'data': {
            'xAxis': times,
            'series': [
                {
                    'name': ip,
                    'type': 'line',
                    'data': data_dir
                }
            ]
        }
    }
    return JsonResponse(result)


def get_mem_chartdata(request):
    """
    获取内存数据
    """
    ip = request.GET.get('ip')
    task_name = request.GET.get('task_name')
    capacitydatas = Operation.objects.filter(task=task_name, ip=ip, result=True)
    times = []
    data_dir = []
    for capacity in capacitydatas:
        times.append(capacity.start_time.strftime('%Y-%m-%d %H:%M:%S'))
        data = capacity.log.split('\n')
        data_dir.append(data[1].strip('%'))

    result = {
        'code': 0,
        'result': True,
        'messge': 'success',
        'data': {
            'xAxis': times,
            'series': [
                {
                    'name': ip,
                    'type': 'line',
                    'data': data_dir
                }
            ]
        }
    }
    return JsonResponse(result)
