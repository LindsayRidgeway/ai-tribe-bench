#!/usr/bin/env python3
"""A conversation page: pick a participant, type a message, read the reply.

    python3 lab/chat.py                 # then open http://127.0.0.1:8770
    python3 lab/chat.py --port 9000

Why this exists. §5 of the sheet said a conversation needs desktop Goose, and the founder's objection was
the smallest and most useful one in the whole review: "not on a phone". A page with a drop list and two
boxes is the whole feature, and it works on a phone because it is a page.

What it is NOT. It is not a chat with an engine. Every message is a real wake through `wake/wake.py --ask`:
the participant reads its own identity, state and journal, one call is made, the reply is written into its
output and filed on the shelf, and a `talk:` commit lands. That is slower and more expensive than a chat
box, and it is the point — a conversation here is part of the record, so the next wake can read it.

Nothing in this file holds a key. The key comes from the environment of the shell that started the server,
under the one name the project uses: TRIBE_API_KEY_<VENDOR>. If it is missing the page says so in one
sentence rather than failing in production.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMBERS = ROOT / "wake" / "members"
PAGE = ROOT / "chat.html"
VERDICT = re.compile(r"=== verdict: ([^=]+)===")


def members(root: Path = MEMBERS) -> list[str]:
    """The names in the drop list: whoever has a state folder and a voice file. Sorted, so the list does not
    reshuffle under the hand of somebody trying to use it."""
    if not root.is_dir():
        return []
    return sorted(d.name for d in root.iterdir()
                  if (d / "state" / "voice.md").is_file() and (d / "state" / "identity.md").is_file())


def voice_of(member: str, root: Path = MEMBERS) -> tuple[str, str]:
    """(api, engine id) from the two lines in voice.md. A member with no voice file is not a member."""
    text = (root / member / "state" / "voice.md").read_text(encoding="utf-8")
    api = re.search(r"^api:\s*(\S+)", text, re.M)
    model = re.search(r"^model:\s*(\S+)", text, re.M)
    if not (api and model):
        raise SystemExit(f"!! {member}'s voice.md needs an 'api:' line and a 'model:' line")
    return api.group(1), model.group(1)


def key_name(api: str) -> str:
    return f"TRIBE_API_KEY_{api.upper()}"


def ask_member(member: str, text: str, root: Path = ROOT, timeout: int = 300) -> dict:
    """One wake, as a reply. Returns {"ok", "reply", "verdict", "path"}.

    The reply is read from the raw JSON the harness wrote, not scraped from stdout: scraping the console
    would break the first time somebody reworded a heading, and this project has already spent a day on
    tools that printed a plausible number from the wrong place."""
    try:
        api, engine = voice_of(member, root / "wake" / "members")
    except SystemExit as e:
        return {"ok": False, "reply": str(e), "verdict": "", "path": ""}
    if not os.environ.get(key_name(api)):
        return {"ok": False, "verdict": "",
                "reply": f"set {key_name(api)} in the shell that started this server, then send again.\n"
                         f"That is the only name this project reads.",
                "path": ""}
    out = root / "wake" / "members" / member / "output"
    before = {p.name for p in out.glob("raw-*.json")}
    proc = subprocess.run(
        [sys.executable, "wake/wake.py", "--member", member, "--api-model", engine,
         "--api-base", api, "--ask", text],
        cwd=root, capture_output=True, text=True, timeout=timeout)
    new = sorted({p.name for p in out.glob("raw-*.json")} - before)
    if not new:
        tail = (proc.stdout or proc.stderr or "").strip().splitlines()[-3:]
        return {"ok": False, "reply": "The wake produced no reply.\n" + "\n".join(tail),
                "verdict": "", "path": ""}
    raw = json.loads((out / new[-1]).read_text(encoding="utf-8"))
    m = VERDICT.search(proc.stdout or "")
    return {"ok": True, "reply": raw.get("content", "").strip(),
            "verdict": m.group(1).strip() if m else "", "path": str(new[-1])}


class Handler(BaseHTTPRequestHandler):
    server_version = "tribe-chat/1.0"

    def log_message(self, fmt, *args):  # quiet: a page, not a server log
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html", "/chat.html"):
            if not PAGE.is_file():
                return self._send(500, b"chat.html is missing next to lab/", "text/plain; charset=utf-8")
            return self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        if self.path == "/members":
            body = json.dumps({"members": members()}).encode()
            return self._send(200, body, "application/json")
        self._send(404, b"no", "text/plain; charset=utf-8")

    def do_POST(self):
        if self.path != "/say":
            return self._send(404, b"no", "text/plain; charset=utf-8")
        n = int(self.headers.get("Content-Length") or 0)
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, b'{"ok":false,"reply":"bad json"}', "application/json")
        who = str(req.get("member") or "").strip()
        text = str(req.get("text") or "").strip()
        if not who or not text:
            return self._send(400, json.dumps({"ok": False, "reply": "pick a participant and type something"}).encode(),
                              "application/json")
        if who not in members():
            return self._send(400, json.dumps({"ok": False, "reply": f"no such participant: {who}"}).encode(),
                              "application/json")
        result = ask_member(who, text)
        result["when"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        self._send(200, json.dumps(result).encode(), "application/json")


def serve(port: int = 8770, host: str = "127.0.0.1") -> None:
    srv = ThreadingHTTPServer((host, port), Handler)
    names = members()
    print(f"tribe chat on http://{host}:{port}  —  {len(names)} participant(s): {', '.join(names) or 'none'}")
    if not names:
        print("!! no participants: expected wake/members/<name>/state/{identity,voice}.md")
    else:
        for n in names:
            api, _ = voice_of(n)
            if not os.environ.get(key_name(api)):
                print(f"!! {n} cannot answer: {key_name(api)} is not set in this shell")
    print("ctrl-c to stop. Every message is a real wake and lands as a commit.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="a conversation page for the tribe")
    ap.add_argument("--port", type=int, default=8770)
    ap.add_argument("--host", default="127.0.0.1",
                    help="127.0.0.1 keeps it on this machine; 0.0.0.0 shows it to your phone on the same wifi")
    ap.add_argument("--members", action="store_true", help="print the drop list and exit")
    a = ap.parse_args(argv)
    if a.members:
        print("\n".join(members()))
        return 0
    serve(a.port, a.host)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
