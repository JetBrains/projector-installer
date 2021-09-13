"""Test products.py module"""
from os.path import dirname, join
from unittest import TestCase

from test.resources.installable_apps import INSTALLABLE_APPS
from projector_installer.products import load_installable_apps_from_file, get_all_product_codes, \
    filter_app_by_name_pattern
from projector_installer.products import Product, IDEKind


class ProductsTest(TestCase):
    """Test products.py module"""

    def test_load_installable_apps_from_file(self) -> None:
        """The load_installable_apps_from_file method must load apps from json file"""
        compatible_ide_json_path = join(dirname(__file__), 'resources/compatible_ide.json')
        self.assertEqual(load_installable_apps_from_file(compatible_ide_json_path),
                         INSTALLABLE_APPS)

    def test_get_all_product_codes(self) -> None:
        """The get_all_product_codes method must return product codes"""
        all_product_codes = 'code=IIC&code=IIU&code=PCC&code=PCP&code=CL&code=GO&code=DG&code=PS&' \
                            'code=WS&code=RM&code=RD&code=PD&code=MPS'
        self.assertEqual(get_all_product_codes(), all_product_codes)

    def test_filter_app_by_name_pattern_exact_match(self) -> None:
        """The filter_app_by_name_pattern method must filter apps by given name"""
        matched_product = [Product('IntelliJ IDEA Community 2020.1.1',
                                   'https://download.jetbrains.com/idea/ideaIC-2020.1.1.tar.gz',
                                   IDEKind.Idea_Community)]
        self.assertEqual(filter_app_by_name_pattern(INSTALLABLE_APPS,
                                                    'IntelliJ IDEA Community 2020.1.1'
                                                    ), matched_product)

    def test_filter_app_by_name_pattern_no_pattern(self) -> None:
        """The filter_app_by_name_pattern method must filter nothing when no pattern provided"""
        self.assertEqual(filter_app_by_name_pattern(INSTALLABLE_APPS), INSTALLABLE_APPS)

    def test_filter_app_by_name_pattern_not_matched_pattern(self) -> None:
        """
        The filter_app_by_name_pattern method must return empty array when pattern matched nothing
        """
        self.assertEqual(filter_app_by_name_pattern(INSTALLABLE_APPS, 'not_matched_pattern'), [])
