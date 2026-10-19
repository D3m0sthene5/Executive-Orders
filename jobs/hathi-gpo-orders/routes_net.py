"""Sequential, robots-aware source adapter using the unchanged shared FetchPool."""
import hashlib
import io
import json
from pathlib import Path
import sys
import re
from urllib.parse import urlsplit, unquote
from datetime import datetime, timezone

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "jobs/_lib"))
import fetch_pool


class RouteNetwork:
    def __init__(self):
        self.out = HERE / "output"
        self.out.mkdir(exist_ok=True)
        self.policy = self.out / "policies"
        self.policy.mkdir(exist_ok=True)
        self.blocked_path = self.out / "BLOCKED_HOSTS.json"
        self.blocked = json.loads(self.blocked_path.read_text()) if self.blocked_path.exists() else {}
        owner = self
        class PolicyPool(fetch_pool.FetchPool):
            def allowed(self, url):
                delay = super().allowed(url)
                owner.additional_policy(url)
                return delay
        self.pool = PolicyPool(HERE / ".cache/routes", workers=1, per_host=1,
                                        min_interval=2, timeout=60, max_bytes=120_000_000,
                                        user_agent="EO-Historical-Research/1.0 (https://github.com/D3m0sthene5/Executive-Orders)",
                                        transport=self.transport)

    def additional_policy(self, url):
        """Honor wildcard/end rules and explicit OpenAI groups as well as stdlib rules."""
        parsed = urlsplit(url)
        policy = self.policy / (parsed.hostname + ".robots.txt")
        if not policy.exists():
            return
        groups, agents, rules = [], [], []
        directives_seen = False
        for raw in policy.read_text(encoding="utf-8", errors="replace").splitlines() + ["User-agent: __end__"]:
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, value = (x.strip() for x in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                if directives_seen:
                    groups.append((agents, rules))
                    agents, rules, directives_seen = [], [], False
                agents.append(value.lower())
            elif agents:
                directives_seen = True
                if key in ("allow", "disallow") and value:
                    rules.append((key == "allow", unquote(value)))
        target = unquote(parsed.path + ("?" + parsed.query if parsed.query else ""))
        for ua in (self.pool.user_agent.lower(), "chatgpt-user", "gptbot"):
            matches = [(max((len(a) if a != "*" else 0) for a in aa if a == "*" or a in ua), rr)
                       for aa, rr in groups if any(a == "*" or a in ua for a in aa)]
            if not matches:
                continue
            specificity = max(s for s, rr in matches)
            matched_rules = []
            for s, rr in matches:
                if s != specificity:
                    continue
                for allow, path in rr:
                    end = path.endswith("$")
                    body = path[:-1] if end else path
                    pattern = "^" + ".*".join(re.escape(p) for p in body.split("*")) + ("$" if end else "")
                    if re.search(pattern, target):
                        matched_rules.append((len(body.replace("*", "")), allow))
            if matched_rules:
                length = max(n for n, allow in matched_rules)
                if not any(allow for n, allow in matched_rules if n == length):
                    raise fetch_pool.FetchError("blocked_by_robots_policy: " + parsed.hostname + " agent=" + ua)

    def note(self, row):
        with (self.out / "ROUTE_ATTEMPTS.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(), **row}, sort_keys=True) + "\n")

    def block(self, host, reason):
        self.blocked[host] = reason
        self.blocked_path.write_text(json.dumps(self.blocked, indent=2) + "\n", encoding="utf-8")

    def transport(self, url, headers, timeout):
        parsed = urlsplit(url)
        host = parsed.hostname
        if host and (host.endswith("hathitrust.org") or host == "hdl.handle.net"):
            raise fetch_pool.FetchError("HathiTrust/handle route excluded; no request sent")
        if host in self.blocked:
            raise fetch_pool.FetchError("Host stopped: " + self.blocked[host])
        status, hs, response = fetch_pool.http_transport(url, headers, timeout)
        if status in (401, 403, 408, 425, 429) or status >= 500 or hs.get("retry-after"):
            response.close()
            self.block(host, "HTTP " + str(status))
            raise fetch_pool.FetchError("Host stopped: HTTP " + str(status))
        if parsed.path == "/robots.txt":
            raw = response.read(500001)
            response.close()
            name = host + ".robots.txt"
            (self.policy / name).write_bytes(raw)
            self.note({"stage": "robots", "url": url, "http_status": status,
                       "sha256": hashlib.sha256(raw).hexdigest(), "path": "policies/" + name})
            return status, hs, io.BytesIO(raw)
        return status, hs, response

    def fetch(self, route, url):
        if urlsplit(url).hostname in self.blocked:
            raise fetch_pool.FetchError("Host already stopped: " + self.blocked[urlsplit(url).hostname])
        try:
            result = self.pool.fetch(url)
            raw = result["body"]
            sample = raw[:100000].decode("utf-8", "replace").lower()
            if any(marker in sample for marker in ("<title>just a moment", "cf-chl-", 'id="challenge-form"', "<title>access denied")):
                self.block(urlsplit(result["final_url"]).hostname, "HTML access challenge")
                raise fetch_pool.FetchError("Host stopped: HTML access challenge")
            self.note({"route": route, "url": url, "result": "fetched", "bytes": result["bytes"], "sha256": result["sha256"]})
            return result
        except Exception as exc:
            self.note({"route": route, "url": url, "result": "failed", "reason": str(exc)})
            raise

    def json(self, route, url):
        result = self.fetch(route, url)
        return json.loads(result["body"].decode("utf-8-sig")), result
