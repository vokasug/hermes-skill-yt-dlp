#!/usr/bin/env python3
"""Download via yt-dlp -> ~/result-yt-dlp/YYYY-MM-DD_<title>.<ext>

Date prefix = date of launch (YYYY-MM-DD). Passes --js-runtimes node (skill rule:
yt-dlp only enables deno by default, node must be explicit).

YouTube 429/bot: retries with player_client=android,ios,tv, then Safari cookies,
then both. Extra yt-dlp flags: --cookies-from-browser, --extractor-args, or after --.
"""
import argparse
import datetime
import pathlib
import subprocess
import sys
import time

OUT_DIR = pathlib.Path.home() / "result-yt-dlp"
SKIP_SUFFIXES = (".part", ".ytdl", ".tmp")
YT_DLP = "yt-dlp"
YOUTUBE_PLAYER_CLIENTS = "youtube:player_client=android,ios,tv"


def is_youtube_url(url: str) -> bool:
    u = url.lower()
    return "youtube.com" in u or "youtu.be" in u


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("urls", nargs="+", help="video/page URL(s)")
    ap.add_argument("-f", "--format", default=None, help="yt-dlp -f selector")
    ap.add_argument("-S", "--quality", default=None, help="yt-dlp -S sort, e.g. res:720")
    ap.add_argument("--audio", action="store_true", help="extract mp3 (-x --audio-format mp3)")
    ap.add_argument("--playlist", action="store_true",
                    help="allow full playlist download (default --no-playlist)")
    ap.add_argument("--cookies-from-browser", default=None, metavar="BROWSER",
                    help="yt-dlp --cookies-from-browser, e.g. safari")
    ap.add_argument("--extractor-args", default=None,
                    help="yt-dlp --extractor-args, e.g. youtube:player_client=android,ios,tv")
    ap.add_argument("passthrough", nargs=argparse.REMAINDER,
                    help="extra yt-dlp args after --")
    return ap.parse_args(argv)


def passthrough_args(passthrough):
    extra = list(passthrough or [])
    if extra and extra[0] == "--":
        extra = extra[1:]
    return extra


def build_cmd(args, *, cookies=None, extractor_args=None, today=None):
    today = today or datetime.date.today().isoformat()
    cookies = args.cookies_from_browser if cookies is None else cookies
    extractor_args = args.extractor_args if extractor_args is None else extractor_args
    cmd = [YT_DLP, "--js-runtimes", "node"]
    cmd += ["--yes-playlist"] if args.playlist else ["--no-playlist"]
    if args.audio:
        cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
    if args.format:
        cmd += ["-f", args.format]
    if args.quality:
        cmd += ["-S", args.quality]
    if cookies:
        cmd += ["--cookies-from-browser", cookies]
    if extractor_args:
        cmd += ["--extractor-args", extractor_args]
    cmd += passthrough_args(args.passthrough)
    if args.playlist:
        cmd += ["-o", f"{OUT_DIR}/{today}_%(playlist_title).100B/%(playlist_index)03d - %(title).150B.%(ext)s"]
    else:
        cmd += ["-o", f"{OUT_DIR}/{today}_%(title).150B.%(ext)s"]
    cmd += args.urls
    return cmd


def fallback_attempts(args):
    """(cookies, extractor_args) pairs: as requested, then YouTube ladder."""
    seen = set()

    def add(cookies, ext):
        key = (cookies, ext)
        if key in seen:
            return False
        seen.add(key)
        return True

    cookies0 = args.cookies_from_browser
    ext0 = args.extractor_args
    if add(cookies0, ext0):
        yield cookies0, ext0
    if not any(is_youtube_url(u) for u in args.urls):
        return
    has_clients = bool(ext0 and "player_client" in ext0)
    has_cookies = bool(cookies0)
    if not has_clients and add(cookies0, YOUTUBE_PLAYER_CLIENTS):
        yield cookies0, YOUTUBE_PLAYER_CLIENTS
    if not has_cookies and add("safari", ext0):
        yield "safari", ext0
    both_c, both_e = cookies0 or "safari", ext0 or YOUTUBE_PLAYER_CLIENTS
    if add(both_c, both_e):
        yield both_c, both_e


def self_test():
    args = parse_args(["--audio", "https://youtu.be/AAAAAAAAAAA"])
    cmd = build_cmd(args, today="2026-09-21")
    assert cmd[:3] == ["yt-dlp", "--js-runtimes", "node"], cmd
    assert "--no-playlist" in cmd and "-x" in cmd
    assert cmd[-1].endswith("AAAAAAAAAAA")
    attempts = list(fallback_attempts(args))
    assert attempts[0] == (None, None), attempts
    assert (None, YOUTUBE_PLAYER_CLIENTS) in attempts
    assert ("safari", None) in attempts
    assert ("safari", YOUTUBE_PLAYER_CLIENTS) in attempts
    assert len(attempts) == 4, attempts

    with_flags = parse_args([
        "--cookies-from-browser", "safari",
        "--extractor-args", YOUTUBE_PLAYER_CLIENTS,
        "https://youtu.be/AAAAAAAAAAA",
    ])
    cmd2 = build_cmd(with_flags, today="2026-09-21")
    assert "--cookies-from-browser" in cmd2 and "safari" in cmd2
    assert "--extractor-args" in cmd2
    assert list(fallback_attempts(with_flags)) == [("safari", YOUTUBE_PLAYER_CLIENTS)]

    extra = parse_args([
        "--audio", "https://example.com/v",
        "--", "--sponsorblock-remove", "sponsor",
    ])
    cmd3 = build_cmd(extra, today="2026-09-21")
    assert "--sponsorblock-remove" in cmd3 and "sponsor" in cmd3
    assert list(fallback_attempts(extra)) == [(None, None)]
    print("SELFTEST OK")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv == ["--self-test"]:
        self_test()
        return 0

    args = parse_args(argv)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    t0 = time.time() - 2
    rc = 1
    attempts = list(fallback_attempts(args))
    for i, (cookies, extractor_args) in enumerate(attempts):
        cmd = build_cmd(args, cookies=cookies, extractor_args=extractor_args, today=today)
        if i:
            print(f"retry {i}/{len(attempts)-1}: cookies={cookies!r} extractor-args={extractor_args!r}",
                  file=sys.stderr)
        rc = subprocess.run(cmd).returncode
        if rc == 0:
            break

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
        for p in sorted(OUT_DIR.rglob(f"{today}_*")):
            if p.is_file() and not p.name.endswith(SKIP_SUFFIXES):
                print(f"EXISTS {p} ({p.stat().st_size // 1024} KiB)")
    if rc != 0:
        print(f"yt-dlp exit code: {rc}", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
