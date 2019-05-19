# -*- coding: utf-8 -*-
from ..base import ComponentAPI


class CollectionsDIM(object):
    """Collections of DIM APIS"""

    def __init__(self, client):
        self.client = client

        self.get_dfinfo = ComponentAPI(
            client=self.client, method='GET',
            path='/api/c/self-service-api/dim/get_dfinfo_lisir/',
            description=u'磁盘信息查询'
        )