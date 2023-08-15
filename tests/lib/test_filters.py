from unittest import TestCase
from unittest.mock import Mock

from rapid.lib.filters import ObjectFilters


class TestFilters(TestCase):

    def test_attribute_filter(self):
        foobar = Mock(something='foobar')
        foobar_2 = Mock(something='foobar')
        this_way = Mock(something='this way')
        comes = Mock(something='comes')

        objects = [foobar, this_way, comes]

        self.assertEqual([foobar], ObjectFilters.by_attribute('something', 'foobar', objects))

        objects.append(foobar_2)

        self.assertEqual([foobar, foobar_2], ObjectFilters.by_attribute('something', 'foobar', objects))
        self.assertEqual([this_way], ObjectFilters.by_attribute('something', 'this way', objects))

