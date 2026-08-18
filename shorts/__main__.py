from __future__ import annotations

import argparse
import logging
import sys

from shorts.config import CHANNELS, DEFAULT_CHANNEL, load_dotenv


def main(argv: list | None = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="shorts", description="유튜브 쇼츠 로컬 파이프라인")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pick_p = sub.add_parser("pick", help="RSS에서 미사용 헤드라인 1개 고르고 out/<channel>/ 잡 생성")
    pick_p.add_argument(
        "--channel",
        default=DEFAULT_CHANNEL,
        choices=list(CHANNELS),
        help="out/<channel>/<job> (기본 %s)" % DEFAULT_CHANNEL,
    )
    sub.add_parser("auth", help="YouTube OAuth (1회)")

    render_p = sub.add_parser("render", help="ffmpeg 정지컷 + 자막 + BGM (줌 없음)")
    render_p.add_argument("--dir", help="잡 폴더 out/<channel>/<job>")

    meta_p = sub.add_parser("meta", help="Studio에 붙일 제목·설명·해시태그·태그 출력")
    meta_p.add_argument("--dir", help="잡 폴더 out/<channel>/<job>")

    upload_p = sub.add_parser("upload", help="YouTube videos.insert")
    upload_p.add_argument("--dir", help="잡 폴더 out/<channel>/<job>")
    upload_p.add_argument("--dry-run", action="store_true", help="업로드 생략")

    run_p = sub.add_parser("run", help="결정적 단계: 필요 시 pick → render → 조건부 업로드")
    run_p.add_argument("--dir", help="잡 폴더 out/<channel>/<job>")
    run_p.add_argument(
        "--channel",
        default=None,
        choices=list(CHANNELS),
        help="--dir 없을 때 채널 (없으면 열린 잡 전체 검색, 새 pick은 %s)" % DEFAULT_CHANNEL,
    )
    run_p.add_argument("--dry-run", action="store_true", help="업로드 생략, 로컬 mp4+JSON만")

    record_p = sub.add_parser("record", help="youtube.uploads 상태 기록 (Studio 업로드 후)")
    record_p.add_argument("--dir", required=True, help="잡 폴더 out/<channel>/<job>")
    record_p.add_argument(
        "--status",
        default="uploaded",
        choices=["picked", "rendered", "uploaded", "failed", "deleted"],
    )
    record_p.add_argument("--video-id", default="", help="YouTube video id")

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    try:
        if args.cmd == "pick":
            from shorts.run import cmd_pick

            cmd_pick(args.channel)
        elif args.cmd == "auth":
            from shorts.upload import auth

            auth()
        elif args.cmd == "render":
            from shorts.run import cmd_render

            cmd_render(args.dir)
        elif args.cmd == "meta":
            from shorts.run import cmd_meta

            cmd_meta(args.dir)
        elif args.cmd == "upload":
            from shorts.run import cmd_upload

            cmd_upload(args.dir, dry_run=args.dry_run)
        elif args.cmd == "run":
            from shorts.run import cmd_run

            cmd_run(args.dir, dry_run=args.dry_run, channel=args.channel)
        elif args.cmd == "record":
            from shorts.run import cmd_record

            cmd_record(args.dir, args.status, video_id=args.video_id)
        else:
            parser.print_help()
            return 2
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        if exc.code:
            print(exc.code, file=sys.stderr)
            return 1
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
