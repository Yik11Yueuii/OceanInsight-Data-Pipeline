import unittest
import csv
import tempfile
from pathlib import Path

from oceaninsight.generate import _indicator, filter_vessel_master


class GenerateTests(unittest.TestCase):
    def test_packaged_indicator_directory(self):
        path = Path("source/ocean_nc/temperature/file.nc")
        self.assertEqual(_indicator(path), "temperature")

    def test_original_indicator_directory(self):
        path = Path("source/1-temperature/file.nc")
        self.assertEqual(_indicator(path), "temperature")

    def test_filter_vessel_master_replaces_existing_lineage_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            master = root / "master.csv"
            activity = root / "vessel_activity_2021.csv"
            output = root / "output.csv"

            with master.open("w", encoding="utf-8", newline="") as target:
                writer = csv.DictWriter(
                    target,
                    fieldnames=["mmsi", "year", "name", "batch_id", "source_file"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "mmsi": "100000110",
                        "year": "2021",
                        "name": "demo",
                        "batch_id": "old-batch",
                        "source_file": "old.csv",
                    }
                )

            with activity.open("w", encoding="utf-8", newline="") as target:
                writer = csv.DictWriter(target, fieldnames=["mmsi", "year"])
                writer.writeheader()
                writer.writerow({"mmsi": "100000110", "year": "2021"})

            stats = filter_vessel_master(
                master,
                [activity],
                output,
                "student-vessel-master",
            )

            with output.open(encoding="utf-8", newline="") as source:
                rows = list(csv.DictReader(source))
                fieldnames = list(rows[0].keys())

            self.assertEqual(
                fieldnames,
                ["mmsi", "year", "name", "batch_id", "source_file"],
            )
            self.assertEqual(rows[0]["batch_id"], "student-vessel-master")
            self.assertEqual(rows[0]["source_file"], "master.csv")
            self.assertEqual(stats["output_rows"], 1)


if __name__ == "__main__":
    unittest.main()
