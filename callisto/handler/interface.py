import tornado.web

from callisto import get_logger
from callisto.handler.dlna import logger
from callisto.service.communicator import Action, CommunicationData

logger = get_logger(__name__)


class InterfaceHandler(tornado.web.RequestHandler):
    """
    server に対して処理を指示したり状況を確認したりする制御用サーバ
    注: data_received method を実装しろという warning が出るけどとりあえずスルー
      - https://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler.data_received
    """
    def initialize(self, service):
        self.service = service

    def get(self):
        self.render('index.html')

    def post(self):
        logger.debug(self.request.arguments)
        action = self.get_argument('action')

        if action == 'connection':
            logger.debug('request connection to STB')
            # STB との接続を要求
            data = CommunicationData(action=Action.STB_START_CONNECTION)
            self.service.add(data)
        elif action == 'power':
            logger.debug('request power on/off')
            data = CommunicationData(action=Action.STB_TOGGLE_POWER)
            self.service.add(data)
        elif action == 'channel':
            channel = self.get_argument('channel')
            if channel == 'discovery':
                logger.debug('request channel discovery')
                data = CommunicationData(action=Action.STB_CHANNEL_DISCOVERY)
                self.service.add(data)

        self.redirect(self.request.uri, status=303)
