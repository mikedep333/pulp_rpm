import shutil
from tempfile import mkdtemp
from urlparse import urljoin

from nectar.config import DownloaderConfig
from pulp.plugins.cataloger import Cataloger

from pulp_rpm.plugins.db import models
from pulp_rpm.plugins.importers.yum.repomd.metadata import MetadataFiles
from pulp_rpm.plugins.importers.yum.repomd import primary, nectar_factory
from pulp_rpm.plugins.importers.yum.repomd import packages


TYPE_ID = 'yum'


def entry_point():
    """
    The Pulp platform uses this method to load the cataloger.
    :return: YumCataloger class and an (empty) config
    :rtype:  tuple
    """
    return YumCataloger, {}


class YumCataloger(Cataloger):

    @classmethod
    def metadata(cls):
        return {
            'id': TYPE_ID,
            'display_name': "Yum Cataloger",
            'types': [models.RPM.TYPE]
        }

    @staticmethod
    def _add_packages(conduit, base_url, md_files):
        """
        Add package (rpm) entries to the catalog.
        :param conduit: Access to pulp platform API.
        :type conduit: pulp.server.plugins.conduits.cataloger.CatalogerConduit
        :param base_url: The base download URL.
        :type base_url: str
        :param md_files: The metadata files object.
        :type md_files: pulp_rpm.plugins.importers.yum.repomd.metadata.MetadataFiles
        """
        fp = md_files.get_metadata_file_handle(primary.METADATA_FILE_NAME)
        try:
            _packages = packages.package_list_generator(
                fp, primary.PACKAGE_TAG, primary.process_package_element)
            for model in _packages:
                unit_key = model.unit_key
                url = urljoin(base_url, model.download_path)
                conduit.add_entry(models.RPM.TYPE, unit_key, url)
        finally:
            fp.close()

    def downloader(self, conduit, config, url):
        """
        Get object suitable for downloading content published
        in the content catalog by a content source.
        :param conduit: Access to pulp platform API.
        :type conduit: pulp.server.plugins.conduits.cataloger.CatalogerConduit
        :param config: The content source configuration.
        :type config: dict
        :param url: The URL for the content source.
        :type url: str
        """
        nectar_config = DownloaderConfig(**config)
        return nectar_factory.create_downloader(url, nectar_config)

    def refresh(self, conduit, config, url):
        """
        Refresh the content catalog.
        :param conduit: Access to pulp platform API.
        :type conduit: pulp.server.plugins.conduits.cataloger.CatalogerConduit
        :param config: The content source configuration.
        :type config: dict
        :param url: The URL for the content source.
        :type url: str
        """
        dst_dir = mkdtemp()
        nectar_config = DownloaderConfig(**config)
        try:
            md_files = MetadataFiles(url, dst_dir, nectar_config)
            md_files.download_repomd()
            md_files.parse_repomd()
            md_files.download_metadata_files()
            self._add_packages(conduit, url, md_files)
        finally:
            shutil.rmtree(dst_dir)