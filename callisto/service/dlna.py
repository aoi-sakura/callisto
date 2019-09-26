# -*- coding: utf-8 -*-
from enum import Enum
import logging
import time

import tornado
from tornado.queues import Queue

from callisto import get_logger
from callisto.libs.protocol.dlna import ssdp

logger = get_logger(__name__)


class Action(Enum):
    START_SSDP_NOTIFY = 1
    STOP_SSDP_NOTIFY = 2
    CONTINUE_SSDP_NOTIFY = 3
    SSDP_M_SEARCH = 4


class CommunicationData:
    def __init__(self, action, args=None):
        self.action = action
        self.args = args


class DlnaService:
    def __init__(self, device_info_url, ssdp_notify_timeout):
        self.__queue = Queue(maxsize=10)
        self.device_info_url = device_info_url
        self.ssdp_notify_timeout = ssdp_notify_timeout

        self.is_continue_notify = False

    def is_start_ssdp_notify(self):
        return self.is_continue_notify

    def add(self, comm_data: CommunicationData):
        self.__queue.put(comm_data)

    def post(self, comm_data: CommunicationData):
        result = []
        if comm_data.action == Action.SSDP_M_SEARCH:
            if not self.is_continue_notify:
                logger.warning('not start SSDP NOTIFY yet')

            response = ssdp.msearch()
            logger.debug('post msearch')
            logger.debug(response)

            for response_item in response:
                result_item = dict()
                for line in response_item.split('\r\n'):
                    key_val = line.split(':', 1)
                    if len(key_val) == 2:
                        [key, val] = key_val
                        result_item[key.lower()] = val.strip()
                result.append(result_item)

        else:
            logger.error('No action selected')

        return result

    async def run(self):
        async for item in self.__queue:
            try:
                if item.action == Action.START_SSDP_NOTIFY:
                    self.is_continue_notify = True
                    ssdp.notify(ssdp.NTS.BYEBYE, self.device_info_url)
                    self.add(CommunicationData(Action.CONTINUE_SSDP_NOTIFY))
                if item.action == Action.STOP_SSDP_NOTIFY:
                    self.is_continue_notify = False
                if item.action == Action.CONTINUE_SSDP_NOTIFY:
                    if self.is_continue_notify:
                        ssdp.notify(ssdp.NTS.ALIVE, self.device_info_url)
                        await tornado.gen.sleep(self.ssdp_notify_timeout)
                        self.add(CommunicationData(Action.CONTINUE_SSDP_NOTIFY))
                    else:
                        ssdp.notify(ssdp.NTS.BYEBYE, self.device_info_url)
                if item.action == Action.SSDP_M_SEARCH:
                    # M-SEARCH はここで処理しない、なぜなら communicator.py:run loop では同期的に response が欲しいから
                    # (というか、非同期でここで処理して、予備元に帰って来させるのが面倒くさい...とても)
                    #
                    # ToDo: dlna.py を communicator.py に統合して queue を処理する loop は一つにするべきか
                    #       そうしないと、結局 SSDP_NOTIFY の response を受けた後、次の処理に進むのが作れない
                    # ToDo: 統合においての懸念は、START_CONNECTION_STB というビジネスレイヤーと START_SSDP_NOTIFY という実装レイヤーの
                    #       呼び出しが混ざってしまう事、これは避けたい
                    # MEMO: loop を一つにできないなら、複数の loop を監視して橋渡しをする処理を用意するか...
                    # ToDo: Pub/Sub なんかだとそういう界面の異なるメッセージの処理とかどうしているんだろ
                    pass
            finally:
                self.__queue.task_done()
