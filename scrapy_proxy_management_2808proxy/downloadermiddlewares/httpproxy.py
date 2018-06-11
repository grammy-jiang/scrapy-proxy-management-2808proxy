from scrapy.exceptions import NotConfigured
from scrapy.settings import SETTINGS_PRIORITIES
from scrapy.utils.httpobj import urlparse_cached
from six.moves.urllib.request import getproxies, proxy_bypass

from scrapy_proxy_management_2808proxy import unfreeze_settings, \
    get_proxy
from scrapy_proxy_management_2808proxy.settings import default_settings


class HttpProxyMiddleware(object):

    def __init__(self, auth_encoding='latin-1'):
        self.auth_encoding = auth_encoding
        self.proxies = {}
        for type_, url in getproxies().items():
            self.proxies[type_] = get_proxy(url, type_, self.auth_encoding)

    @classmethod
    def from_crawler(cls, crawler):
        with unfreeze_settings(crawler.settings) as settings:
            settings.setmodule(
                module=default_settings,
                priority=SETTINGS_PRIORITIES['default']
            )
        if not crawler.settings.getbool('HTTPPROXY_ENABLED'):
            raise NotConfigured

        auth_encoding = crawler.settings.get('HTTPPROXY_AUTH_ENCODING')
        return cls(auth_encoding)

    def process_request(self, request, spider):
        # ignore if proxy is already set
        if 'proxy' in request.meta:
            if request.meta['proxy'] is None:
                return
            # extract credentials if present
            creds, proxy_url = get_proxy(request.meta['proxy'], '', self.auth_encoding)
            request.meta['proxy'] = proxy_url
            if creds and not request.headers.get('Proxy-Authorization'):
                request.headers['Proxy-Authorization'] = b'Basic ' + creds
            return
        elif not self.proxies:
            return

        parsed = urlparse_cached(request)
        scheme = parsed.scheme

        # 'no_proxy' is only supported by http schemes
        if scheme in ('http', 'https') and proxy_bypass(parsed.hostname):
            return

        if scheme in self.proxies:
            self._set_proxy(request, scheme)

    def _set_proxy(self, request, scheme):
        creds, proxy = self.proxies[scheme]
        request.meta['proxy'] = proxy
        if creds:
            request.headers['Proxy-Authorization'] = b'Basic ' + creds
