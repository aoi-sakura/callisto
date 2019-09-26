# -*- coding: utf-8 -*-
import tornado.web

from callisto import get_logger
from callisto.const import *
from callisto.service.communicator import Action as CommuAction, CommunicationData as CommuData

logger = get_logger(__name__)


class DeviceInfoHandler(tornado.web.RequestHandler):
    """
    Device に関する情報を返すためのサーバ
    """
    def initialize(self, service):
        self.service = service

    def get(self):
        self.set_header('Server', LOCAL_SERVER_HEADER_NAME)
        self.clear_header('Etag')

        # ToDo: リクエスト元の通信をチェックし、STB の場合、STB に接続できる状態であることを伝える
        logger.debug(self.request)

        return self.render(FILENAME_REMOTE_CONTROLLER_XML)
