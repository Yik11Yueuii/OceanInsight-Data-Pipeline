import unittest

from oceaninsight.core import current_metrics, depth_level, grid_cell, iter_months, normalize_lon


class CoreTests(unittest.TestCase):
    def test_longitude(self):
        self.assertEqual(normalize_lon(200), -160)
        self.assertEqual(normalize_lon(120), 120)

    def test_grid(self):
        self.assertEqual(grid_cell(11.9, 121.9), (10.0, 120.0, "g2_+010.0_+0120.0"))

    def test_depth(self):
        self.assertEqual(depth_level(1), "SURFACE")
        self.assertEqual(depth_level(1000), "DEEP")

    def test_current(self):
        speed, direction = current_metrics(1, 0)
        self.assertAlmostEqual(speed, 1)
        self.assertAlmostEqual(direction, 90)

    def test_months(self):
        self.assertEqual(list(iter_months("2020-11", "2021-02")), ["2020-11", "2020-12", "2021-01", "2021-02"])


if __name__ == "__main__":
    unittest.main()

