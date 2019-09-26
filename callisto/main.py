# -*- coding: utf-8 -*-

import os
import logging
import argparse
import tornado
from tornado.netutil import bind_sockets
from tornado.httpserver import HTTPServer

from callisto import get_logger
from callisto.const import *
from callisto.service.communicator import CommunicatorService, CommunicationData, Action as CommunicatorAction
from callisto.service.dlna import DlnaService
from callisto.handler.dlna import DeviceInfoHandler
from callisto.handler.interface import InterfaceHandler
from callisto.handler.jlabs import JLabsSpecHandler

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
}

logger = get_logger(__name__)


def configure():
    result = dict()
    parser = argparse.ArgumentParser(description='STB remote control server')
    parser.add_argument('-i', '--host', dest='host', metavar='host',
                        type=str, required=True,
                        help='host IP address')
    result['host'] = parser.parse_args().host
    result['ssdp_notify_timeout'] = 600
    return result


def build_device_info_url(conf):
    location = 'http://{host}:{port}/{device_info_path}'.format(
        host=conf['host'],
        port=PORT_DEVICE_INFO,
        device_info_path=FILENAME_REMOTE_CONTROLLER_XML)
    conf['device_info_url'] = location
    return conf


if __name__ == '__main__':
    config = configure()
    config = build_device_info_url(config)

    dlnaService = DlnaService(config['device_info_url'], config['ssdp_notify_timeout'])
    commuService = CommunicatorService(dlnaService, config['host'], FAKE_USER_AGENT, TARGET_SERVER_HEADER_NAME)

    interface_sockets = bind_sockets(PORT_INTERFACE)
    device_info_sockets = bind_sockets(PORT_DEVICE_INFO)
    jlabs_spec_sockets = bind_sockets(PORT_JLABS_SPEC)
    # bind_sockets 後に必要, 必ず 1 をセットする。複数プロセスで動くように作っていない
    tornado.process.fork_processes(1)

    interface_app = tornado.web.Application(
        handlers=[(r'/remocon', InterfaceHandler, dict(service=commuService))],
        **settings)
    interface_server = HTTPServer(interface_app)
    interface_server.add_sockets(interface_sockets)

    device_info_app = tornado.web.Application(
        handlers=[(r'/' + FILENAME_REMOTE_CONTROLLER_XML, DeviceInfoHandler, dict(service=commuService))],
        **settings)
    device_info_server = HTTPServer(device_info_app)
    device_info_server.add_sockets(device_info_sockets)

    jlabs_spec_server = JLabsSpecHandler(service=commuService)
    jlabs_spec_server.add_sockets(jlabs_spec_sockets)

    tornado.ioloop.IOLoop.current().spawn_callback(dlnaService.run)
    tornado.ioloop.IOLoop.current().spawn_callback(commuService.run)

    # STB への接続シーケンス開始
    logger.info("request to connect STB.")
    commuService.add(CommunicationData(CommunicatorAction.STB_START_CONNECTION))

    logger.info("start service")
    tornado.ioloop.IOLoop.current().start()
