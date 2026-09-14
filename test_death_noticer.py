"""Tests for death-noticer. All Docker I/O is mocked — no daemon needed."""

import json
import unittest
from unittest import mock

import death_noticer as dn


DIE_EVENT = json.dumps({
    "Type": "container", "Action": "die",
    "Actor": {"Attributes": {"name": "my-api"}},
})

START_EVENT = json.dumps({"Type": "container", "Action": "start",
                          "Actor": {"Attributes": {"name": "my-api"}}})

INSPECT = [{
    "Name": "/my-api",
    "Config": {"Image": "api:1.2"},
    "State": {
        "Status": "exited", "ExitCode": 137, "OOMKilled": True, "Error": "",
        "StartedAt": "2026-09-14T02:58:00Z", "FinishedAt": "2026-09-14T03:01:30Z",
    },
    "RestartCount": 3,
}]


class FakeSh:
    def __init__(self, logs=""):
        self.logs = logs

    def __call__(self, args, timeout=60):
        if args[:2] == ["docker", "inspect"]:
            return True, json.dumps(INSPECT), ""
        if args[:2] == ["docker", "logs"]:
            return True, self.logs, ""
        return True, "", ""


class TestRules(unittest.TestCase):
    def test_oom_cause_wins(self):
        self.assertIn("OOMKilled", dn.cause_of_death({"exit_code": 1, "oom_killed": True}))

    def test_exit_137(self):
        self.assertIn("SIGKILL", dn.cause_of_death({"exit_code": 137, "oom_killed": False}))

    def test_unknown_exit(self):
        self.assertIn("42", dn.cause_of_death({"exit_code": 42, "oom_killed": False}))


class TestObituary(unittest.TestCase):
    def test_has_sections_and_logs(self):
        text = dn.obituary({"container": "my-api", "image": "api:1.2", "exit_code": 137,
                            "oom_killed": True, "restart_count": 3,
                            "finished_at": "2026-09-14T03:01:30Z", "uptime": "0:03:30",
                            "logs": ["ERROR: Cannot allocate memory"]})
        self.assertIn("Obituary", text)
        self.assertIn("Cause of death", text)
        self.assertIn("memory pressure", text)
        self.assertIn("Cannot allocate memory", text)
        self.assertIn("death-noticer", text)

    def test_no_logs_no_fence(self):
        text = dn.obituary({"container": "x", "image": "x", "exit_code": 0, "oom_killed": False,
                            "restart_count": 0, "finished_at": "", "uptime": None, "logs": []})
        self.assertNotIn("```", text)


class TestHandleEvent(unittest.TestCase):
    def _args(self, **kw):
        ns = mock.Mock()
        ns.tail = 20
        ns.ai = False
        ns.webhook = None
        ns.reports_dir = kw.get("rd", "/tmp/dn-test")
        return ns

    def test_ignores_non_die_events(self):
        self.assertIsNone(dn.handle_event(START_EVENT, self._args()))

    def test_ignores_garbage(self):
        self.assertIsNone(dn.handle_event("not json", self._args()))

    def test_writes_obituary_on_die(self):
        import tempfile, os
        rd = tempfile.mkdtemp()
        with mock.patch.object(dn, "sh", FakeSh(logs="FATAL: connection refused")), \
             mock.patch.object(dn.time, "sleep"):
            report = dn.handle_event(DIE_EVENT, self._args(rd=rd))
        self.assertIsNotNone(report)
        self.assertIn("connection refused", report)
        files = os.listdir(rd)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].startswith("my-api-"))

    def test_webhook_called_on_die(self):
        import tempfile
        rd = tempfile.mkdtemp()
        ns = self._args(rd=rd)
        ns.webhook = "http://example.invalid/hook"
        with mock.patch.object(dn, "sh", FakeSh()), mock.patch.object(dn.time, "sleep"), \
             mock.patch.object(dn, "notify") as n:
            dn.handle_event(DIE_EVENT, ns)
        self.assertTrue(n.called)


class TestNotify(unittest.TestCase):
    def test_notify_swallows_network_errors(self):
        self.assertFalse(dn.notify("http://127.0.0.1:1/hook", "report"))


class TestCli(unittest.TestCase):
    def test_single_container_mode(self):
        with mock.patch.object(dn, "sh", FakeSh()):
            rc = dn.main(["my-api"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
