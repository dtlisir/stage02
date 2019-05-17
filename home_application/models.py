# -*- coding: utf-8 -*-

from django.db import models


class Operation(models.Model):
    user = models.CharField(max_length=50)
    task = models.CharField(max_length=60, default="unknown")
    start_time = models.DateTimeField(auto_now_add=True)
    biz = models.CharField(max_length=30)
    ip = models.CharField(max_length=30)
    celery_id = models.CharField(max_length=100)
    status = models.CharField(max_length=30, default="queue")
    log = models.TextField(null=True, blank=True)
    result = models.BooleanField(default=False)
    end_time = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.user + self.task

    class Meta:
        ordering = ['-id']

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user,
            'task': self.task,
            'start_time': self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            'biz': self.biz,
            'ip': self.ip,
            'celery_id': self.celery_id,
            'status': self.status,
            'end_time': self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else "",
        }
