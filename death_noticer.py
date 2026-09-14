#!/usr/bin/env python3
"""
death-noticer — your containers die at 3 AM. Someone should notice.

An always-on Docker sidecar that watches `docker events`. The instant any
container dies it writes a markdown obituary (cause of death, evidence, last
logs) and optionally posts it to Slack/Discord/any webhook. Zero dependencies,
deterministic rules first, local AI epilogue second.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

__version__ = "1.0.0"

EXIT_CODES = {
    0: "🌱 finished its job on purpose — nothing kept it alive",
    1: "💥 application error — the traceback is usually in the last logs",
    2: "💥 shell/CLI misuse — bad CMD/ENTRYPOINT arguments",
    125: "🐳 Docker daemon failed to run it",
    126: "🔒 command exists but is not executable (chmod +x?)",
    127: "🔍 command not found — binary missing from the image",
    137: "🗡️ SIGKILL — kernel OOM killer or docker stop -f timeout",
    139: "☠️ segfault — native code dereferenced bad memory",
    143: "🛑 SIGTERM — orchestrated stop or reschedule",
}

LOG_PATTERNS = [
    (re.compile(r"out of memory|oom|cannot allocate memory|killed process", re.I), "🧠 memory pressure in logs"),
    (re.compile(r"connection refused|econnrefused", re.I), "🔌 a dependency refused the connection"),
    (re.compile(r"timeout|etimedout", re.I), "⏱️ an upstream call timed out"),
    (re.compile(r"permission denied|eperm|eacces", re.I), "🔒 permission denied in logs"),
    (re.compile(r"no such file|enoent", re.I), "📁 a file was missing at runtime"),
    (re.compile(r"traceback \(most recent call last\)", re.I), "🐍 unhandled Python exception"),
    (re.compile(r"panic:|runtime error", re.I), "🟦 Go panic"),
    (re.compile(r"health ?check failed|unhealthy", re.I), "🩺 health checks were failing"),
]


def sh(args, timeout=60):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode == 0, p.stdout, p.stderr
    except FileNotFoundError:
        sys.exit("error: docker CLI not found in PATH. Run death-noticer in its official image.")
    except subprocess.TimeoutExpired:
        return False, "", "timeout"


def autopsy(container, tail):
    """Collect read-only evidence for one container."""
    ok, out, err = sh(["docker", "inspect", container])
    if not ok:
        return None
    info = json.loads(out)[0]
    state = info.get("State", {})
    _, logs, _ = sh(["docker", "logs", "--tail", str(tail), container])
    uptime = None
    try:
        t0 = datetime.fromisoformat(state.get("StartedAt", "")[:19])
        t1 = datetime.fromisoformat(state.get("FinishedAt", "")[:19])
        if t1.year > 1:
            uptime = str(t1 - t0).split(".")[0]
    except ValueError:
        pass
    return {
        "container": info.get("Name", container).lstrip("/"),
        "image": info.get("Config", {}).get("Image", "?"),
        "exit_code": state.get("ExitCode"),
        "oom_killed": state.get("OOMKilled", False),
        "restart_count": info.get("RestartCount", 0),
        "finished_at": state.get("FinishedAt", ""),
        "uptime": uptime,
        "logs": logs.strip().splitlines()[-tail:],
    }


def cause_of_death(data):
    if data["oom_killed"]:
        return "🗡️ OOMKilled — it exceeded its memory limit and the kernel ended it"
    return EXIT_CODES.get(data["exit_code"], "❓ unknown exit code %s" % data["exit_code"])


def obituary(data):
    """Render the markdown obituary."""
    clues = [title for pattern, title in LOG_PATTERNS if any(pattern.search(l) for l in data["logs"])][:1]
    when = data["finished_at"][:19].replace("T", " ") or "unknown time"
    lines = [
        "## 🕯️ Obituary — `%s`" % data["container"],
        "",
        "*%s, beloved service behind `%s`, left us at %s after %s of uptime, surviving %s restart(s).*" % (
            data["container"], data["image"], when, data["uptime"] or "unknown", data["restart_count"]),
        "",
        "**Cause of death:** %s" % cause_of_death(data),
    ]
    if clues:
        lines.append("**Final words:** %s" % clues[0])
    if data["logs"]:
        lines += ["", "```", *data["logs"][-8:], "```"]
    lines += ["", "*In lieu of flowers, raise the memory limit.* 🪦 "
              "Noticed by [death-noticer](https://github.com/fernedy/death-noticer)"]
    return "\n".join(lines) + "\n"


def notify(webhook, report):
    """Post an obituary to Slack/Discord/generic webhook. Best effort, never fatal."""
    try:
        body = json.dumps({"content": report[:1900], "text": report[:1900]}).encode()
        req = urllib.request.Request(webhook, data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:  # noqa: BLE001 — a dead notifier must never join the deceased
        print("warn: webhook delivery failed: %s" % e, file=sys.stderr)
        return False


def handle_event(line, args):
    """Process one docker events JSON line. Returns obituary text or None."""
    try:
        ev = json.loads(line)
    except json.JSONDecodeError:
        return None
    if ev.get("Action") != "die" or ev.get("Type") != "container":
        return None
    name = ev.get("Actor", {}).get("Attributes", {}).get("name") or ev.get("id", "")[:12]
    time.sleep(1)  # let the engine settle exit code / final logs
    data = autopsy(name, args.tail)
    if data is None:
        return None
    report = obituary(data)
    if args.ai:
        ok, out, _ = sh(["opencode", "run", "You are an SRE. Add a 3-line 'AI epilogue' to this "
                                          "container obituary: likely root cause, confirm command, fix command.\n\n" + report])
        if ok:
            report += "\n### 🤖 AI epilogue\n" + out.strip() + "\n"
    if args.webhook:
        notify(args.webhook, report)
    os.makedirs(args.reports_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = os.path.join(args.reports_dir, "%s-%s.md" % (data["container"], stamp))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(report)
    print("🕯️ noticed the death of '%s' -> %s" % (data["container"], path))
    return report


def watch(args):
    """Follow docker events forever."""
    proc = subprocess.Popen(["docker", "events", "--format", "{{json .}}"],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    print("death-noticer %s watching docker events (reports in %s)..." % (__version__, args.reports_dir))
    for line in proc.stdout:
        handle_event(line, args)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="death-noticer",
                                 description="Your containers die at 3 AM. Someone should notice.")
    ap.add_argument("--reports-dir", default="./reports", help="where obituaries are written (default ./reports)")
    ap.add_argument("--webhook", default=None, help="Slack/Discord/generic webhook URL to post obituaries")
    ap.add_argument("--tail", type=int, default=20, help="log lines per obituary (default 20)")
    ap.add_argument("--ai", action="store_true", help="add a local AI epilogue via opencode")
    ap.add_argument("container", nargs="?", help="with this arg: write one obituary for this container and exit")
    ap.add_argument("--version", action="version", version="%(prog)s " + __version__)
    args = ap.parse_args(argv)

    if args.container:
        data = autopsy(args.container, args.tail)
        if data is None:
            sys.exit("error: cannot inspect '%s'" % args.container)
        print(obituary(data))
        return 0
    watch(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
