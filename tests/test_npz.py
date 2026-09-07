import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from oceaninsight.npz import inspect_npz


class NpzTests(unittest.TestCase):
    def test_metadata_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sample.npz"
            output = root / "report.json"
            np.savez_compressed(source, values=np.array([[1.0, np.nan], [3.0, 5.0]]))

            report = inspect_npz(source, output)

            self.assertEqual(report["arrays"]["values"]["shape"], [2, 2])
            self.assertEqual(report["arrays"]["values"]["finite_elements"], 3)
            self.assertEqual(report["arrays"]["values"]["missing_elements"], 1)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), report)


if __name__ == "__main__":
    unittest.main()
