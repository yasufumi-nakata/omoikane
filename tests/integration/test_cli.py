from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from omoikane.cli import main


class CliIntegrationTests(unittest.TestCase):
    def test_connectome_demo_emits_valid_json(self) -> None:
        stdout = io.StringIO()

        with patch("sys.argv", ["omoikane", "connectome-demo", "--json"]), redirect_stdout(stdout):
            main()

        result = json.loads(stdout.getvalue())
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(result["ledger_verification"]["ok"])
        self.assertEqual(3, result["validation"]["node_count"])


if __name__ == "__main__":
    unittest.main()
