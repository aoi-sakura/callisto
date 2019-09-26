import socket
import logging
from enum import Enum

from callisto import get_logger

logger = get_logger(__name__)


class NTS(Enum):
    ALIVE = 1
    BYEBYE = 2


NOTIFY_REQUEST_LINES = (
    'NOTIFY * HTTP/1.1',
    'HOST: {host}',
    'CACHE-CONTROL: max-age={cache_age}',
    'LOCATION: {location}',
    'NT: urn:schemas-upnp-org:device:MediaServer:1',
    'NTS: ssdp:{nts}',
    'SERVER: P01MA/6.0.1 UPnP-Device-Host/1.0',
    'USN: uuid:ed53864f-b16f-49d5-8f45-2d95e2a00df6::urn:schemas-upnp-org:device:MediaServer:1',
    '',
    '')

MSEARCH_REQUEST_LINES = (
    'M-SEARCH * HTTP/1.1',
    'HOST: {host}',
    'MAN: "ssdp:discover"',
    'MX: 3',
    'ST: urn:schemas-upnp-org:device:MediaServer:1',
    '',
    '')


def notify(nts, location, cache_age=1800, broadcast_host='239.255.255.250', broadcast_port=1900):
    if nts == NTS.ALIVE:
        nts = 'alive'
    elif nts == NTS.BYEBYE:
        nts = 'byebye'

    req = '\r\n'.join(NOTIFY_REQUEST_LINES).format(
        nts=nts,
        location=location,
        host='{}:{}'.format(broadcast_host, broadcast_port),
        cache_age=cache_age)
    return __postrequest(req, broadcast_host, broadcast_port)


def msearch(broadcast_host='239.255.255.250', broadcast_port=1900):
    req = '\r\n'.join(MSEARCH_REQUEST_LINES).format(
        host='{}:{}'.format(broadcast_host, broadcast_port))
    return __postrequest(req, broadcast_host, broadcast_port)


def __postrequest(request, broadcast_host, broadcast_port, charcode='utf-8'):
    result = []
    timeout = 5
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    sock.sendto(request.encode(charcode), (broadcast_host, broadcast_port))
    # ToDo: これ、目的を果たしたら while loop から抜けるべきやがな...
    while True:
        try:
            res, device = sock.recvfrom(4096)
            logger.debug('SSDP response from %s' % (device,))
            logger.debug(res)

            if res is not None:
                res = res.decode(charcode)

            result.append(res)
        except socket.timeout:
            logger.warning('socket timeout')
            break
        except OSError as e:
            logger.warning(e)
            break
    sock.close()
    return result
