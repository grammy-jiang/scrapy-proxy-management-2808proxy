import base64
from contextlib import contextmanager

from scrapy.utils.python import to_bytes
from six.moves.urllib.parse import unquote, urlunparse

try:
    from urllib2 import _parse_proxy
except ImportError:
    from urllib.request import _parse_proxy


@contextmanager
def unfreeze_settings(settings):
    original_status = settings.frozen
    settings.frozen = False
    try:
        yield settings
    finally:
        settings.frozen = original_status


def basic_auth_header(username, password, auth_encoding):
    user_pass = to_bytes(
        '{}:{}'.format(unquote(username), unquote(password)),
        encoding=auth_encoding)
    return base64.b64encode(user_pass).strip()


def get_proxy(url, orig_type, auth_encoding):
    proxy_type, user, password, host_port = _parse_proxy(url)
    proxy_url = urlunparse((proxy_type or orig_type, host_port, '', '', '', ''))

    if user:
        creds = basic_auth_header(user, password, auth_encoding)
    else:
        creds = None

    return creds, proxy_url
