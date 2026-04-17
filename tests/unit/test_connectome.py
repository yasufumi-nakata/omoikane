from __future__ import annotations

import unittest

from omoikane.mind.connectome import ConnectomeModel


class ConnectomeModelTests(unittest.TestCase):
    def test_reference_snapshot_validates(self) -> None:
        model = ConnectomeModel()

        document = model.build_reference_snapshot("identity-demo")
        validation = model.validate(document)

        self.assertTrue(validation["ok"])
        self.assertEqual(3, validation["node_count"])
        self.assertEqual(2, validation["edge_count"])
        self.assertEqual("identity-demo", validation["identity_id"])

    def test_validate_rejects_edge_to_unknown_node(self) -> None:
        model = ConnectomeModel()
        document = model.build_reference_snapshot("identity-demo")
        document["edges"][0]["target"] = "8e34af7e-f4ee-490b-ae59-db95d2fa29d8"

        with self.assertRaisesRegex(ValueError, "unknown node"):
            model.validate(document)

    def test_validate_rejects_duplicate_node_id(self) -> None:
        model = ConnectomeModel()
        document = model.build_reference_snapshot("identity-demo")
        document["nodes"][1]["id"] = document["nodes"][0]["id"]

        with self.assertRaisesRegex(ValueError, "duplicate node id"):
            model.validate(document)


if __name__ == "__main__":
    unittest.main()
