import unittest


class TestWillFail(unittest.TestCase):
    def test_failing(self):
        raise Exception('Write some tests please.')
