"""Test products.py module"""
from unittest import TestCase

from projector_installer.products import get_all_product_codes, \
    filter_app_by_name_pattern, COMPATIBLE_IDE_FILE, load_compatible_apps
from projector_installer.products import Product, IDEKind


class ProductsTest(TestCase):
    """Test products.py module"""
    COMPATIBLE_APPS = load_compatible_apps(COMPATIBLE_IDE_FILE)

    def test_get_all_product_codes(self) -> None:
        """The get_all_product_codes method must return product codes"""
        all_product_codes = 'code=IIC&code=IIU&code=PCC&code=PCP&code=CL&code=GO&code=DG&code=PS&' \
                            'code=WS&code=RM&code=RD&code=PCD&code=MPS'
        self.assertEqual(get_all_product_codes(), all_product_codes)

    def test_filter_app_by_name_pattern_exact_match(self) -> None:
        """The filter_app_by_name_pattern method must filter apps by given name"""
        matched_product = [Product('IntelliJ IDEA Community Edition 2020.1',
                                   'https://download.jetbrains.com/idea/ideaIC-2020.1.4.tar.gz',
                                   IDEKind.Idea_Community)]
        self.assertEqual(filter_app_by_name_pattern(self.COMPATIBLE_APPS,
                                                    'IntelliJ IDEA Community Edition 2020.1'
                                                    ), matched_product)

    def test_filter_app_by_name_pattern_no_pattern(self) -> None:
        """The filter_app_by_name_pattern method must filter nothing when no pattern provided"""
        self.assertEqual(filter_app_by_name_pattern(self.COMPATIBLE_APPS), self.COMPATIBLE_APPS)

    def test_filter_app_by_name_pattern_not_matched_pattern(self) -> None:
        """
        The filter_app_by_name_pattern method must return empty array when pattern matched nothing
        """
        self.assertEqual(filter_app_by_name_pattern(self.COMPATIBLE_APPS,
                                                    'not_matched_pattern'), [])
