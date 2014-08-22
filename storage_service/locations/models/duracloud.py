# stdlib, alphabetical
import os

# Core Django, alphabetical
from django.db import models

# Third party dependencies, alphabetical
import requests

# This project, alphabetical

# This module, alphabetical
from . import StorageException
from location import Location


class Duracloud(models.Model):
    space = models.OneToOneField('Space', to_field='uuid')
    host = models.CharField(max_length=256,
        help_text='Hostname of the DuraCloud instance. Eg. trial.duracloud.org')
    user = models.CharField(max_length=64, help_text='Username to authenticate as')
    password = models.CharField(max_length=64, help_text='Password to authenticate with')
    duraspace = models.CharField(max_length=64, help_text='Name of the Space within DuraCloud')

    class Meta:
        verbose_name = "DuraCloud"
        app_label = 'locations'

    ALLOWED_LOCATION_PURPOSE = [
        Location.AIP_STORAGE,
        Location.DIP_STORAGE,
        Location.TRANSFER_SOURCE,
        Location.BACKLOG,
    ]

    def __init__(self, *args, **kwargs):
        super(Duracloud, self).__init__(*args, **kwargs)
        self._session = None

    @property
    def session(self):
        if self._session is None:
            self._session = requests.Session()
            self._session.auth = (self.user, self.password)
        return self._session

    @property
    def duraspace_url(self):
        return 'https://' + self.host + '/durastore/' + self.duraspace + '/'

    def move_to_storage_service(self, src_path, dest_path, dest_space):
        """ Moves src_path to dest_space.staging_path/dest_path. """
        pass

    def _upload_file(self, url, upload_file):
        # Example URL: https://trial.duracloud.org/durastore/trial261//ts/test.txt
        with open(upload_file, 'rb') as f:
            response = self.session.put(url, data=f)
        if response.status_code != 201:
            raise StorageException('Unable to store %s' % upload_file)

    def move_from_storage_service(self, source_path, destination_path):
        """ Moves self.staging_path/src_path to dest_path. """
        if os.path.isdir(source_path):
            # Both source and destination paths should end with /
            destination_path = os.path.join(destination_path, '')
            # Duracloud does not accept folders, so upload each file individually
            for path, _, files in os.walk(source_path):
                for basename in files:
                    entry = os.path.join(path, basename)
                    dest = entry.replace(source_path, destination_path, 1)
                    url = self.duraspace_url + dest
                    self._upload_file(url, entry)
        elif os.path.isfile(source_path):
            url = self.duraspace_url + destination_path
            self._upload_file(url, source_path)
        elif not os.path.exists(source_path):
            raise StorageException('%s does not exist.' % source_path)
        else:
            raise StorageException('%s is not a file or directory.' % source_path)