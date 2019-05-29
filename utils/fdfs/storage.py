from django.core.files.storage import Storage
from django.conf import settings

from fdfs_client.client import Fdfs_client


class FDFSStorage(Storage):

    def __init__(self, client_conf=None, base_url=None):
        """
        :param client_conf:
        :param base_url:
        """
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        # name:选择上传文件的名字
        # content:包含上传文件内容的File对象

        # 创建Fdfs_client对象
        client = Fdfs_client(self.client_conf)

        # 上传文件到fast dfs系统中
        res = client.upload_by_buffer(content.read())
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # } if success else None
        if res.get('Status') != 'Upload successed.':
            raise Exception('上传文件失败')

        # 获取返回的文件id
        filename = res.get('Remote file_id')

        return filename

    def exists(self, name):
        """
        Returns True if a file referenced by the given name already exists in the
        storage system, or False if the name is available for a new file.
        """
        return False

    def url(self, name):

        return self.base_url + name

