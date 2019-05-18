# -*- coding: utf-8 -*-

import base64
import time
import datetime
from config import APP_CODE, SECRET_KEY
from blueking.component.shortcuts import get_client_by_request
from django.http import JsonResponse


def get_dfinfo_lisir(request):
    try:
        biz_id = request.POST.get("biz_id")
        ip = request.POST.get("ip")
        os_name = request.POST.get("os_name")
        partition = request.POST.get("partition")
        content = "df -h | awk '($6==\"%s\"){print $5}'" % partition
        script_content = base64.b64encode(content.encode('utf-8'))
        kwargs = {
            "bk_app_code": APP_CODE,
            "bk_app_secret": SECRET_KEY,
            "bk_biz_id": biz_id,
            "script_content": str(script_content, 'utf-8'),
            "script_param": "",
            "ip_list": [{"bk_cloud_id": 0, "ip": ip}],
            "script_type": 1,
            "account": "root"
        }
        client = get_client_by_request(request)
        result = client.job.fast_execute_script(kwargs)
        if result["result"]:
            script_result = get_job_instance_log(client, biz_id, result["data"]["job_instance_id"])
            return script_result
        else:
            return JsonResponse({"result": "false", "message": result["message"], "data": {}})
    except Exception as e:
        return JsonResponse({"result": "false", "message": str(e), "data": {}})


def get_job_instance_log(client, biz_id, job_id):
    kwargs = {
        "bk_app_code": APP_CODE,
        "bk_app_secret": SECRET_KEY,
        "bk_biz_id": biz_id,
        "job_instance_id": job_id
    }
    result = client.job.get_job_instance_log(kwargs)
    if result["result"]:
        if result["data"][0]["is_finished"]:
            if result["data"][0]["status"] == 3:
                log_content = result["data"][0]["step_results"][0]["ip_logs"][0]["log_content"]
                return JsonResponse({
                    "result": "true",
                    "message": "Script run success.",
                    "data": {"log_content": log_content, "time": datetime.datetime.now()}
                })
            else:
                return JsonResponse({
                    "result": "false",
                    "message": "Script run failed,error code is:{}".format(result["data"][0]["status"]),
                    "data": {}
                })
        else:
            time.sleep(3)
            return get_job_instance_log(client, biz_id, job_id)

    else:
        return JsonResponse({"result": "false", "message": result["message"]})
