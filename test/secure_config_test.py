"""Test secure_config.py module"""
import os
from os.path import expanduser

from unittest import TestCase

from projector_installer.secure_config import get_ca_ini_file, create_ca_ini, \
    get_ca_jks_backup_file, make_ca_backup, restore_ca_backup, remove_ca_backup, get_ca_password
from projector_installer.version import __version__

class SecureConfigTest(TestCase):
    """Test secure_config.py module"""

    user = expanduser('~')

    def test_get_ca_ini_file(self) -> None:
        """The get_ca_ini_file method must return a path to ca.ini file"""
        ca_ini_file = f'{self.user}/.projector/ssl/ca.ini'
        self.assertEqual(get_ca_ini_file(), ca_ini_file)

    def test_create_ca_ini(self) -> None:
        """The create_ca_ini method must create ca.ini file with provided token"""
        ssl_dir_path = f'{self.user}/.projector/ssl'
        os.makedirs(ssl_dir_path)

        ca_ini_file = f'{self.user}/.projector/ssl/ca.ini'
        open(ca_ini_file, 'a').close()

        create_ca_ini(token='token')

        with open(ca_ini_file, 'r') as configfile:
            self.assertEqual(configfile.read(), '[CA]\nsaved = token\n\n')

        os.remove(ca_ini_file)
        os.removedirs(ssl_dir_path)

    def test_get_ca_jks_backup_file(self) -> None:
        """The get_ca_jks_backup_file method must return a path to ca.jks.backup file"""
        ca_jks_backup_file = f'{self.user}/.projector/ssl/ca.jks.backup'
        self.assertEqual(get_ca_jks_backup_file(), ca_jks_backup_file)

    def test_make_ca_backup(self) -> None:
        """The make_ca_backup method must create a backup of ca.jks file"""
        ssl_dir_path = f'{self.user}/.projector/ssl'
        os.makedirs(ssl_dir_path)

        ca_jks_file = f'{self.user}/.projector/ssl/ca.jks'
        open(ca_jks_file, 'w').close()

        self.assertTrue(make_ca_backup())

        ca_jks_backup_file = f'{self.user}/.projector/ssl/ca.jks.backup'
        self.assertTrue(os.path.exists(ca_jks_backup_file))

        os.remove(ca_jks_file)
        os.remove(ca_jks_backup_file)
        os.removedirs(ssl_dir_path)

    def test_make_ca_backup_no_file_exists(self) -> None:
        """The make_ca_backup method must return false when source file doesn't exist"""
        ssl_dir_path = f'{self.user}/.projector/ssl'
        os.makedirs(ssl_dir_path)

        self.assertFalse(make_ca_backup())

        os.removedirs(ssl_dir_path)

    def test_restore_ca_backup(self) -> None:
        """The restore_ca_backup method must restore ca.jks file from backup"""
        ssl_dir_path = f'{self.user}/.projector/ssl'
        os.makedirs(ssl_dir_path)

        ca_jks_backup_file = f'{self.user}/.projector/ssl/ca.jks.backup'
        open(ca_jks_backup_file, 'w').close()

        self.assertTrue(restore_ca_backup())

        ca_jks_file = f'{self.user}/.projector/ssl/ca.jks'
        self.assertTrue(os.path.exists(ca_jks_file))

        os.remove(ca_jks_file)
        os.remove(ca_jks_backup_file)
        os.removedirs(ssl_dir_path)

    def test_restore_ca_backup_no_backup_file_exists(self) -> None:
        """The restore_ca_backup method must return false when backup file doesn't exist"""
        ssl_dir_path = f'{self.user}/.projector/ssl'
        os.makedirs(ssl_dir_path)

        self.assertFalse(restore_ca_backup())

        os.removedirs(ssl_dir_path)

    def test_remove_ca_backup(self) -> None:
        """
        The remove_ca_backup method must return true when deletion of backup file was successful
        """
        ssl_dir_path = f'{self.user}/.projector/ssl'
        os.makedirs(ssl_dir_path)

        ca_jks_backup_file = f'{self.user}/.projector/ssl/ca.jks.backup'
        open(ca_jks_backup_file, 'w').close()

        self.assertTrue(remove_ca_backup())
        self.assertFalse(os.path.exists(ca_jks_backup_file))

        os.removedirs(ssl_dir_path)

    def test_remove_ca_backup_no_backup_file_exists(self) -> None:
        """The remove_ca_backup method must return false when backup file doesn't exist"""
        ssl_dir_path = f'{self.user}/.projector/ssl'
        os.makedirs(ssl_dir_path)

        self.assertFalse(remove_ca_backup())

        os.removedirs(ssl_dir_path)

    def test_get_ca_password(self) -> None:
        """The get_ca_password method must return ca password"""
        self.assertEqual(get_ca_password(), '85TibAyPS3NZX3')

    def test_get_ca_password_no_ca_ini_file_exists(self) -> None:
        """The get_ca_password method must return token located in ca.ini file"""
        ssl_dir_path = f'{self.user}/.projector/ssl'
        os.makedirs(ssl_dir_path)

        ca_ini_file = f'{self.user}/.projector/ssl/ca.ini'
        open(ca_ini_file, 'a').close()

        create_ca_ini(token='token')

        self.assertEqual(get_ca_password(), 'token')

        os.remove(ca_ini_file)
        os.removedirs(ssl_dir_path)
