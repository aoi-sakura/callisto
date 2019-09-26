# -*- coding: utf-8 -*-
import json

from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError

from callisto import get_logger
from callisto.service.communicator import CommunicationData, Action

logger = get_logger(__name__)

END_OF_TRANSACTION = b'\x04'


class JLabsSpecHandler(TCPServer):
    """
    接続確立後、STB と通信するサーバ
    """

    def __init__(self, service=None, ssl_options=None, max_buffer_size=None, read_chunk_size=None):
        super().__init__(ssl_options, max_buffer_size, read_chunk_size)

        self.service = service

    async def handle_stream(self, stream, address):
        while True:
            try:
                request = await stream.read_until(END_OF_TRANSACTION)
                if not request:
                    break
                # logger.debug(request)
            except StreamClosedError as e:
                logger.error("StreamCloseError occurred!")
                logger.error(e)
                break
            except Exception as e:
                logger.error("Exception occurred!")
                logger.error(e)
                break
            data = JLabsSpecHandler.__pre_process(request)

            # address から stream を service 側で構築しようと思ったけど、結局同じものを作るので stream をそのまま渡す
            # ToDo: 毎回渡す必要は無いけど、排他入れるの面倒だしで、毎回書き換えさせてる
            # self.service.add(CommunicationData(Action.STB_SAVE_JLABS_SERVER_INFO, address))
            self.service.add(CommunicationData(Action.STB_SAVE_JLABS_SERVER_INFO, stream))
            logger.debug(data)
            self.__handling_json(data)

    @staticmethod
    def __pre_process(data):
        data = data.decode('utf-8', "backslashreplace")
        # [:-1] しているのは、\x04 が含まれているからそれを削除している
        return data[:-1]

    def __handling_json(self, data):
        js = json.loads(data)
        self.service.add(CommunicationData(Action.JLABS_DATA_FROM_STB, js))
