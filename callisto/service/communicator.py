# -*- coding: utf-8 -*-
from enum import Enum
import json

import tornado
from tornado.queues import Queue

from callisto import get_logger
from callisto.libs.protocol import jlabs as jlabs_protocol
from callisto.service.dlna import Action as DlnaAction, CommunicationData as DlnaCommuData

logger = get_logger(__name__)


class Action(Enum):
    STB_START_CONNECTION = 1
    STB_STOP_CONNECTION = 2

    STB_SAVE_JLABS_SERVER_INFO = 3
    JLABS_DATA_FROM_STB = 4

    STB_TOGGLE_POWER = 10
    STB_CHANNEL_DISCOVERY = 20


class CommunicationData:
    def __init__(self, action, args=None):
        self.action = action
        self.args = args


class Channel(Enum):
    DISCOVERY = 1


class CommunicatorService:
    def __init__(self, dlna_service, host, ua, target_server_name):
        self.__queue = Queue(maxsize=10)
        self.dlna_service = dlna_service

        # TODO: プロパティ式にあとで変換して書き換えられないようにする
        self.ua = ua
        self.target_server_name = target_server_name
        self.is_start_ssdp_notify = self.dlna_service.is_start_ssdp_notify

        self.host = host
        # jLabs プロトコルでやりトルする為の client
        self.jlabs_client = None

    def add(self, comm_data: CommunicationData):
        self.__queue.put(comm_data)

    async def run(self):
        async for item in self.__queue:
            try:
                if item.action == Action.STB_START_CONNECTION:
                    self.dlna_service.add(DlnaCommuData(DlnaAction.START_SSDP_NOTIFY))
                    # ToDo: sleep ではなく、SSDP NOTIFY のレスポンスがあった事をトリガに次に進ませたい
                    logger.debug('pre sleep')
                    await tornado.gen.sleep(5)
                    logger.debug('post sleep')
                    # これにより STB 側の接続先を取得する
                    response = self.dlna_service.post(DlnaCommuData(DlnaAction.SSDP_M_SEARCH))
                    logger.debug('post msearch')
                    for res_item in response:
                        logger.debug(res_item)
                        logger.debug('location: %s' % res_item['location'])
                        logger.debug('server: %s' % res_item['server'])
                        if res_item['server'] == self.target_server_name:
                            location = res_item['location']
                            # ToDo: ↑で取得した STB 側の接続先を HTTP で叩く
                            response = jlabs_protocol.get_stb_info(location, self.ua)
                            logger.debug('get_stb_info response')
                            logger.debug(response)
                            break

                    # この後は 5090 port にアクセスが来るのでそっちで処理開始

                elif item.action == Action.STB_STOP_CONNECTION:
                    self.dlna_service.add(DlnaCommuData(DlnaAction.STOP_SSDP_NOTIFY))
                elif item.action == Action.STB_SAVE_JLABS_SERVER_INFO:
                    # 5080 port の server の loop から stream をそのまま持ってきている
                    # MEMO: そのまますぎるので、正直設計的には汚い
                    server_address = item.args
                    self.jlabs_client = server_address
                elif item.action == Action.JLABS_DATA_FROM_STB:
                    self.__handle_jlabs(item.args)

                elif item.action == Action.STB_TOGGLE_POWER:
                    # 電源ボタンが押されるのと同じアクション
                    self.__request_jlsbs_send_key("VK_POWER")
                elif item.action == Action.STB_CHANNEL_DISCOVERY:
                    # Disovery チャンネルを指定した時のアクション
                    self.__request_jlabs_channel(Channel.DISCOVERY)

            finally:
                self.__queue.task_done()

    def __send_jlabs_client(self, data):
        # MEMO: '\x04' が無いと終端した判定してくれない
        self.jlabs_client.write(json.dumps(data).encode('utf-8') + b'\x04')

    def __request_jlsbs_send_key(self, key_id):
        rc_key_request_json = {"param": {"type": "keypress", "keyCode": key_id},
                               "sequenceID": "rcKey", "request": "rcKey"}
        self.__send_jlabs_client(rc_key_request_json)

    def __request_jlabs_channel(self, channel):
        if channel == Channel.DISCOVERY:
            self.__request_jlsbs_send_key("VK_6")
            self.__request_jlsbs_send_key("VK_5")
            self.__request_jlsbs_send_key("VK_2")
            self.__request_jlsbs_send_key("VK_ENTER")

    def __handle_jlabs(self, args):
        if args.get('request') is not None:
            if args.get('request') == 'startWiFiPairing':
                # 1. startWifiPairing の request を受け取ったら、受け取ったことを示す response を返す
                # 2. そして、次の処理の getMWVersion を呼ぶ
                start_wifi_pairing_response = \
                    {"response": "startWiFiPairing",
                     "sequenceID": args.get('sequenceID'),
                     "result": 1,
                     "errorCode": "",
                     "data": {"permission": True}}
                self.__send_jlabs_client(start_wifi_pairing_response)
                logger.info("Remote Controller service is now available.")

                # ここ以降の処理は、試しで実装しているけどリモコン使うだけなら要らない
                # ToDo: getMWVersion も要らないかどうか確認する

                # 続けて request を飛ばす
                get_mw_version_request = \
                    {"param": {}, "sequenceID": "getMWVersion", "request": "getMWVersion"}
                # MEMO: '\x04' が無いと終端した判定してくれない
                self.__send_jlabs_client(get_mw_version_request)
        elif args.get('response') is not None:
            if args.get('response') == 'getMWVersion':
                # getMWVersion のレスポンスは特にどうでもいい

                # getMWVersion のレスポンスを受け取ったら、次は getReservationList を呼ぶ
                get_reservation_list_request = {"param": {"sort":0},
                                                "sequenceID": "getReservationList",
                                                "request": "getReservationList"}
                # ToDo: リモコン操作には必要ない認識なので、一旦 off
                # await self.__send_jlabs_client(get_reservation_list_request)

            elif args.get('response') == 'getReservationList':
                # getReservationList のレスポンスは今のところ使わない

                # 次にgetChannels を呼ぶ
                get_channels_request = {"param": {"networkType": 0},
                                        "sequenceID": "getChannels",
                                        "request": "getChannels"}
                self.__send_jlabs_client(get_channels_request)

            elif args.get('response') == 'getChannels':
                # 最初は 地上波 のリストを取得
                # その後、BS, CS 分呼ぶ
                # 今の所、特に活用せず
                get_channels_request = {"param": {"networkType": 0},
                                        "sequenceID": "getChannels",
                                        "request": "getChannels"}
                if args.get('data').get('items')[0].get('networkType') == 0:
                    get_channels_request['param']['networkType'] = 1
                    self.__send_jlabs_client(get_channels_request)
                elif args.get('data').get('items')[0].get('networkType') == 1:
                    get_channels_request['param']['networkType'] = 2
                    self.__send_jlabs_client(get_channels_request)
                elif args.get('data').get('items')[0].get('networkType') == 2:
                    # getChannel は終わったので次へ
                    # ToDo: 途中で面倒になったのでいったんここまで
                    pass
