import csv
import tempfile
import unittest
import zipfile
from pathlib import Path

from oceaninsight.vessel import select_zip


class VesselTests(unittest.TestCase):
    def test_stream_selection_and_continuity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "vessel.zip"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(
                    "2019-01-01.csv",
                    "date,cell_ll_lat,cell_ll_lon,mmsi,hours,fishing_hours\n"
                    "2019-01-01,20.1,130.1,123,2,0\n"
                    "2019-01-01,-20,130,456,3,2\n",
                )
            output = root / "selected.csv"
            stats = select_zip(
                source, output,
                {"lat_min": 10, "lat_max": 50, "lon_min": 120, "lon_max": 160},
                2, "test-batch",
            )
            self.assertEqual(stats["input_rows"], 2)
            self.assertEqual(stats["output_rows"], 1)
            with output.open(encoding="utf-8") as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(row["mmsi"], "123")
            self.assertEqual(row["fishing_hours"], "0.0")

