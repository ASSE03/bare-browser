#!/usr/bin/env python3
"""Checks that the whole patch series still applies to the pinned Chromium.

Needs no Chromium checkout. It reads the pinned commit from BUILDING.md,
downloads from the chromium/chromium mirror on GitHub only the files the
series modifies, then applies every patch in filename order with `git apply`.

Files outside the main Chromium repository (V8, Skia and other DEPS
checkouts) are not in the mirror. Hunks touching them are skipped and listed,
not counted as failures.

Usage: python3 tools/check_patches.py [--keep DIR]
Exit code 0 when every patch applies, 1 otherwise.
"""

import argparse
import concurrent.futures
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PATCHES = ROOT / "patches"
RAW = "https://raw.githubusercontent.com/chromium/chromium/{commit}/{path}"


def pinned_commit() -> str:
    text = (ROOT / "BUILDING.md").read_text(encoding="utf-8")
    match = re.search(r"Chromium commit:\s*`([0-9a-f]{40})`", text)
    if not match:
        sys.exit("Pinned Chromium commit not found in BUILDING.md")
    return match.group(1)


def files_needed(patches):
    """Paths the series changes that must already exist in Chromium."""
    created, needed = set(), []
    header = re.compile(r"^diff --git a/(\S+) b/(\S+)$")
    for patch in patches:
        lines = patch.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines):
            m = header.match(line)
            if not m:
                continue
            path = m.group(1)
            block = lines[i + 1 : i + 6]
            is_new = any(l.startswith("new file mode") for l in block) or any(
                l == "--- /dev/null" for l in block
            )
            if is_new:
                created.add(path)
            elif path not in created and path not in needed:
                needed.append(path)
    return needed


def download(commit, path, dest):
    target = dest / path
    target.parent.mkdir(parents=True, exist_ok=True)
    url = RAW.format(commit=commit, path=path)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                target.write_bytes(resp.read())
            return path, True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return path, False
        except (urllib.error.URLError, TimeoutError):
            pass
    raise RuntimeError(f"Could not download {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", help="Keep the patched tree in this directory")
    args = parser.parse_args()

    patches = sorted(PATCHES.glob("*.patch"))
    commit = pinned_commit()
    needed = files_needed(patches)
    print(f"Chromium {commit[:10]}, {len(patches)} patches, {len(needed)} files to fetch")

    work = pathlib.Path(args.keep or tempfile.mkdtemp(prefix="bare-check-"))
    work.mkdir(parents=True, exist_ok=True)
    missing = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        for path, ok in pool.map(lambda p: download(commit, p, work), needed):
            if not ok:
                missing.append(path)
    if missing:
        print(f"{len(missing)} files are outside the chromium mirror and are skipped:")
        for path in missing:
            print(f"  - {path}")

    subprocess.run(["git", "init", "-q", str(work)], check=True)
    excludes = [f"--exclude={p}" for p in missing]
    failed = []
    for patch in patches:
        result = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", *excludes, str(patch)],
            cwd=work,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failed.append(patch.name)
            print(f"FAIL {patch.name}\n{result.stderr.strip()}\n")

    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    if failed:
        print(f"{len(failed)} patch(es) no longer apply: {', '.join(failed)}")
        return 1
    print("All patches apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
