
from logging import getLogger
from urllib2 import urlopen, URLError
from base64 import urlsafe_b64encode

from pulp_rpm.plugins.db import models
from pulp_rpm.plugins.catalogers.yum import YumCataloger


log = getLogger(__name__)


TYPE_ID = 'rhui'

ID_DOC_HEADER = 'X-RHUI-ID'
ID_SIG_HEADER = 'X-RHUI-SIGNATURE'
ID_DOC_URL = 'http://169.254.169.254/latest/dynamic/instance-identity/document'
ID_SIG_URL = 'http://169.254.169.254/latest/dynamic/instance-identity/signature'


def entry_point():
    """
    The Pulp platform uses this method to load the cataloger.
    :return: RHUICataloger class and an (empty) config
    :rtype:  tuple
    """
    return RHUICataloger, {}


class RHUICataloger(YumCataloger):

    @staticmethod
    def load_id():
        """
        Loads and returns the Amazon metadata for identifying the instance.
        :return the AMI ID.
        :rtype str
        """
        try:
            fp = urlopen(ID_DOC_URL)
            try:
                return fp.read()
            finally:
                fp.close()
        except URLError, e:
            log.error('Load amazon ID document failed: %s', str(e))

    @staticmethod
    def load_signature():
        """
        Loads and returns the Amazon signature of hte Amazon identification metadata.
        :return the signature.
        :rtype str
        """
        try:
            fp = urlopen(ID_SIG_URL)
            try:
                return fp.read()
            finally:
                fp.close()
        except URLError, e:
            log.error('Load amazon signature failed: %s', str(e))

    @classmethod
    def metadata(cls):
        return {
            'id': TYPE_ID,
            'display_name': "RHUI Cataloger",
            'types': [models.RPM.TYPE]
        }

    def nectar_config(self, config):
        """
        Get a nectar configuration using the specified content
        content source configuration.
        :param config: The content source configuration.
        :type config: dict
        :return: A nectar downloader configuration
        :rtype: nectar.config.DownloaderConfig
        """
        amazon_id = RHUICataloger.load_id()
        amazon_signature = RHUICataloger.load_signature()
        nectar_config = super(RHUICataloger, self).nectar_config(config)
        headers = nectar_config.headers or {}
        headers[ID_DOC_HEADER] = urlsafe_b64encode(amazon_id)
        headers[ID_SIG_HEADER] = urlsafe_b64encode(amazon_signature)
        nectar_config.headers = headers
        return nectar_config