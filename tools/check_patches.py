#!/usr/bin/env python3
"""Checks that the whole patch series still applies to the pinned Chromium.

Needs no Chromium checkout. It reads the pinned commit from BUILDING.md,
fetches from the chromium/chromium mirror on GitHub only the files the
series modifies, then applies every patch in filename order with `git apply`.

Files outside the main Chromium repository (V8, Skia and other DEPS
checkouts) are not in the mirror. Hunks touching them are skipped and listed,
not counted as failures.

Usage: python3 tools/check_patches.py [--keep DIR]
Exit code 0 when every patch applies, 1 otherwise.
"""

import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PATCHES = ROOT / "patches"
MIRROR = "https://github.com/chromium/chromium"


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


def git(*args, cwd, **kw):
    return subprocess.run(["git", *args], cwd=cwd, check=True, **kw)


def fetch_files(commit, paths, dest):
    """Writes the given Chromium files into dest; returns the paths not in the repo.

    A blobless shallow fetch of the commit brings only its trees (about 20 MB);
    the blobs needed are then fetched by id in a few batched requests. This
    avoids raw.githubusercontent.com, which throttles hundreds of requests.
    """
    store = dest / ".chromium-objects"
    store.mkdir(parents=True, exist_ok=True)
    git("init", "-q", cwd=store)
    git("fetch", "-q", "--no-tags", "--depth", "1", "--filter=blob:none",
        MIRROR, commit, cwd=store)
    listing = git("ls-tree", "-r", "-z", commit, cwd=store,
                  capture_output=True).stdout.decode()
    blobs = {}
    for entry in listing.split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        blobs[path] = meta.split()[2]
    found = [p for p in paths if p in blobs]
    missing = [p for p in paths if p not in blobs]
    ids = [blobs[p] for p in found]
    for i in range(0, len(ids), 200):
        git("-c", "fetch.negotiationAlgorithm=noop", "fetch", "-q", "--no-tags",
            "--no-write-fetch-head", "--filter=blob:none", MIRROR, *ids[i:i + 200],
            cwd=store)
    for path in found:
        target = dest / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git("cat-file", "blob", blobs[path], cwd=store,
                               capture_output=True).stdout)
    shutil.rmtree(store, ignore_errors=True)
    return missing


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
    missing = fetch_files(commit, needed, work)
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
