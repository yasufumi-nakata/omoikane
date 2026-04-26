from __future__ import annotations

import unittest

from omoikane.interface.collective import CollectiveIdentityService


class CollectiveIdentityServiceTests(unittest.TestCase):
    def test_register_open_close_and_dissolve_collective(self) -> None:
        service = CollectiveIdentityService()
        record = service.register_collective(
            collective_identity_id="collective://meridian",
            member_ids=["identity://origin", "identity://peer"],
            purpose="bounded merge for shared planning",
            proposed_name="Collective Meridian",
            council_witnessed=True,
            federation_attested=True,
            guardian_observed=True,
        )
        session = service.open_merge_session(
            collective_id=record["collective_id"],
            imc_session_id="imc://merge-session",
            wms_session_id="wms://shared-session",
            requested_duration_seconds=8.0,
            council_witnessed=True,
            federation_attested=True,
            guardian_observed=True,
            shared_world_mode="shared_reality",
        )
        closed = service.close_merge_session(
            session["merge_session_id"],
            disconnect_reason="bounded merge completed",
            time_in_merge_seconds=7.8,
            resulting_wms_mode="private_reality",
            identity_confirmations={
                "identity://origin": True,
                "identity://peer": True,
            },
        )
        dissolved = service.dissolve_collective(
            record["collective_id"],
            requested_by="identity://origin",
            member_confirmations={
                "identity://origin": True,
                "identity://peer": True,
            },
            reason="members returned to independent subjectivity",
        )
        final_record = service.snapshot(record["collective_id"])
        record_validation = service.validate_record(final_record)
        session_validation = service.validate_merge_session(closed)
        dissolution_validation = service.validate_dissolution_receipt(dissolved)

        self.assertEqual("Collective Meridian", record["display_name"])
        self.assertEqual("completed", closed["status"])
        self.assertTrue(closed["within_budget"])
        self.assertTrue(closed["private_escape_honored"])
        self.assertEqual("1.0", dissolved["schema_version"])
        self.assertEqual("dissolved", dissolved["status"])
        self.assertEqual("dissolved", final_record["status"])
        self.assertTrue(record_validation["ok"])
        self.assertTrue(session_validation["ok"])
        self.assertTrue(session_validation["identity_confirmation_complete"])
        self.assertTrue(dissolution_validation["ok"])
        self.assertTrue(dissolution_validation["schema_version_bound"])
        self.assertTrue(dissolution_validation["member_confirmation_complete"])
        self.assertTrue(dissolution_validation["audit_bound"])

    def test_open_requires_full_oversight(self) -> None:
        service = CollectiveIdentityService()
        record = service.register_collective(
            collective_identity_id="collective://meridian",
            member_ids=["identity://origin", "identity://peer"],
            purpose="bounded merge for shared planning",
            proposed_name="Collective Meridian",
            council_witnessed=True,
            federation_attested=True,
            guardian_observed=True,
        )

        with self.assertRaisesRegex(PermissionError, "federation attestation"):
            service.open_merge_session(
                collective_id=record["collective_id"],
                imc_session_id="imc://merge-session",
                wms_session_id="wms://shared-session",
                requested_duration_seconds=8.0,
                council_witnessed=True,
                federation_attested=False,
                guardian_observed=True,
                shared_world_mode="shared_reality",
            )


if __name__ == "__main__":
    unittest.main()
