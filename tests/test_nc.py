import unittest
from pathlib import Path

from oceaninsight.nc import _year_month


class NcTests(unittest.TestCase):
    def test_padded_month(self):
        self.assertEqual(_year_month(Path("x_year_2017_month_01.nc")), "2017-01")

    def test_unpadded_month(self):
        self.assertEqual(_year_month(Path("x_year_2017_month_1.nc")), "2017-01")


if __name__ == "__main__":
    unittest.main()
