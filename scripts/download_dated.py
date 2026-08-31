#!/usr/bin/env python3
"""Download via yt-dlp -> /Users/alexander/result-yt-dlp/YYYY-MM-DD_<title>.<ext>

Date prefix = date of launch (YYYY-MM-DD). Passes --js-runtimes node (skill rule:
yt-dlp only enables deno by default, node must be explicit).
"""
import argparse
import datetime
import pathlib
import subprocess
import sys
import time

OUT_DIR = pathlib.Path("/Users/alexander/result-yt-dlp")
SKIP_SUFFIXES = (".part", ".ytdl", ".tmp")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("urls", nargs="+", help="video/page URL(s)")
    ap.add_argument("-f", "--format", default=None, help="yt-dlp -f selector")
    ap.add_argument("-S", "--quality", default=None, help="yt-dlp -S sort, e.g. res:720")
    ap.add_argument("--audio", action="store_true", help="extract mp3 (-x --audio-format mp3)")
    ap.add_argument("--playlist", action="store_true",
                    help="allow full playlist download (default --no-playlist)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()

    cmd = ["yt-dlp", "--js-runtimes", "node"]
    cmd += ["--yes-playlist"] if args.playlist else ["--no-playlist"]
    if args.audio:
        cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
    if args.format:
        cmd += ["-f", args.format]
    if args.quality:
        cmd += ["-S", args.quality]
    if args.playlist:
        cmd += ["-o", f"{OUT_DIR}/{today}_%(playlist_title).100B/%(playlist_index)03d - %(title).150B.%(ext)s"]
    else:
        cmd += ["-o", f"{OUT_DIR}/{today}_%(title).150B.%(ext)s"]
    cmd += args.urls

    t0 = time.time() - 2
    rc = subprocess.run(cmd).returncode

    def safe_stat(p: pathlib.Path):
        try:
            return p.stat()
        except OSError:
            return None

    new = sorted(
        p for p in OUT_DIR.rglob("*")
        if p.is_file() and (st := safe_stat(p)) and st.st_mtime >= t0
        and not p.name.endswith(SKIP_SUFFIXES))
    for p in new:
        print(f"OK {p} ({p.stat().st_size // 1024} KiB)")
    if not new and rc == 0:
        # yt-dlp сказал «has already been downloaded» или файл старше окна —
        # перечисляем уже существующие файлы за сегодня
        for p in sorted(OUT_DIR.rglob(f"{today}_*")):
            if p.is_file() and not p.name.endswith(SKIP_SUFFIXES):
                print(f"EXISTS {p} ({p.stat().st_size // 1024} KiB)")
    if rc != 0:
        print(f"yt-dlp exit code: {rc}", file=sys.stderr)
    sys.exit(rc)


if __name__ == "__main__":
    main()
