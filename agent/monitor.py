#!/usr/bin/env python3
"""
Simple File Integrity Monitoring Agent
- Computes SHA-256 hashes for files under a folder.
- Stores baseline in baseline.json (in same folder as this script).
- Detects new/modified/deleted files and POSTs change events to backend /log endpoint.
- Uses only Python stdlib for HTTP so no extra pip packages are required for the agent.

Usage:
    python monitor.py --path /full/path/to/monitor --server http://127.0.0.1:5000 --interval 5

If baseline.json is empty on first run the agent will create it from current state.
"""

import os
import sys
import argparse
import hashlib
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

# Files/dirs to ignore (relative names)
IGNORE_NAMES = {"baseline.json", "integrity_logs.sqlite", ".git", "__pycache__"}


def compute_file_hash(path, chunk_size=8192):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def scan_tree(root):
    """Return dict of relative_path -> hexhash for files under root."""
    root = os.path.abspath(root)
    result = {}
    for dirpath, dirnames, filenames in os.walk(root):
        # mutate dirnames in-place to skip ignored dirs
        dirnames[:] = [d for d in dirnames if d not in IGNORE_NAMES]
        for fn in filenames:
            if fn in IGNORE_NAMES:
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, root)
            # skip the baseline file stored inside agent folder if user monitors root outside agent
            if os.path.basename(rel) in IGNORE_NAMES:
                continue
            h = compute_file_hash(fp)
            if h is not None:
                # normalize path to use forward slashes for consistent display
                result[rel.replace('\\', '/') ] = h
    return result


def load_baseline(bpath):
    try:
        with open(bpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def save_baseline(bpath, data):
    tmp = bpath + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, bpath)


def send_event(server_url, payload, timeout=5):
    url = urllib.parse.urljoin(server_url, "/log")
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read().decode('utf-8', errors='ignore')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def make_event(event_type, relpath, old_hash, new_hash):
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "path": relpath,
        "old_hash": old_hash,
        "new_hash": new_hash,
    }


def main():
    parser = argparse.ArgumentParser(description="File Integrity Monitoring Agent")
    parser.add_argument("--path", "-p", dest="path", default='.', help="Path to monitor (default: current directory)")
    parser.add_argument("--baseline", "-b", dest="baseline", default=os.path.join(os.path.dirname(__file__), "baseline.json"), help="Path to baseline.json (will be created/updated)")
    parser.add_argument("--server", "-s", dest="server", default="http://127.0.0.1:5000", help="Backend server base URL (default http://127.0.0.1:5000)")
    parser.add_argument("--interval", "-i", dest="interval", type=float, default=5.0, help="Scan interval in seconds (default 5)")
    args = parser.parse_args()

    monitor_root = os.path.abspath(args.path)
    baseline_path = os.path.abspath(args.baseline)
    server = args.server.rstrip('/')
    interval = max(0.5, float(args.interval))

    print(f"Monitoring: {monitor_root}")
    print(f"Baseline file: {baseline_path}")
    print(f"Server: {server}")
    print(f"Interval: {interval}s")

    # load baseline
    baseline = load_baseline(baseline_path)
    if not baseline:
        print("No baseline found or baseline empty — creating baseline from current files.")
        baseline = scan_tree(monitor_root)
        save_baseline(baseline_path, baseline)
        print(f"Baseline created with {len(baseline)} files. Next scans will detect changes.")

    try:
        while True:
            current = scan_tree(monitor_root)
            # detect new
            new_files = [p for p in current.keys() if p not in baseline]
            # detect deleted
            deleted_files = [p for p in baseline.keys() if p not in current]
            # detect modified
            modified_files = [p for p in current.keys() if p in baseline and current[p] != baseline[p]]

            events = []
            for p in new_files:
                events.append(make_event("created", p, None, current[p]))
            for p in modified_files:
                events.append(make_event("modified", p, baseline.get(p), current[p]))
            for p in deleted_files:
                events.append(make_event("deleted", p, baseline.get(p), None))

            if events:
                print(f"Detected {len(events)} events — sending to server {server}/log")
                for ev in events:
                    code, resp = send_event(server, ev)
                    if code is None:
                        print(f"Failed to send event for {ev['path']}: {resp}")
                    else:
                        print(f"Server responded ({code}) for {ev['path']}")
                # update baseline to current state after sending
                baseline = current
                save_baseline(baseline_path, baseline)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Agent stopped by user")


if __name__ == '__main__':
    main()
