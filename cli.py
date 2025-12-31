#!/usr/bin/env python3
"""CLI tool for AI Video Workflow project management.

This CLI can be used by Claude or humans to manage the project.

Usage:
    python cli.py status          # Check project status
    python cli.py generate        # Generate new episode
    python cli.py generate 5      # Generate episode 5
    python cli.py history         # View episode history
    python cli.py history 20      # View last 20 episodes
    python cli.py migrate         # Run database migrations
    python cli.py cleanup         # Dry-run cleanup
    python cli.py cleanup --execute  # Actually delete old files
    python cli.py init            # Initialize database
    python cli.py upload-test video.mp4  # Test YouTube upload
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def main():
    parser = argparse.ArgumentParser(
        description="AI Video Workflow Project Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Check project status")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate a new episode")
    generate_parser.add_argument(
        "episode",
        type=int,
        nargs="?",
        help="Episode number (optional, auto-increments if not specified)",
    )
    generate_parser.add_argument(
        "--private",
        action="store_true",
        help="Upload as private video (for testing)",
    )

    # History command
    history_parser = subparsers.add_parser("history", help="View episode history")
    history_parser.add_argument(
        "limit",
        type=int,
        nargs="?",
        default=10,
        help="Number of episodes to show (default: 10)",
    )

    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Run database migrations")
    migrate_parser.add_argument(
        "--action",
        choices=["upgrade", "downgrade", "current", "history"],
        default="upgrade",
        help="Migration action (default: upgrade)",
    )
    migrate_parser.add_argument(
        "--revision",
        default="head",
        help="Target revision (default: head)",
    )

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old files")
    cleanup_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Delete files older than N days (default: 7)",
    )
    cleanup_parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete files (default is dry-run)",
    )

    # Init command
    subparsers.add_parser("init", help="Initialize database")

    # YouTube auth command
    subparsers.add_parser("youtube-auth", help="Get new YouTube refresh token")

    # Upload test command
    upload_parser = subparsers.add_parser("upload-test", help="Test YouTube upload with a video file")
    upload_parser.add_argument(
        "video_path",
        type=str,
        help="Path to video file to upload",
    )
    upload_parser.add_argument(
        "--title",
        type=str,
        default="테스트 영상",
        help="Video title (default: '테스트 영상')",
    )
    upload_parser.add_argument(
        "--description",
        type=str,
        default="YouTube 업로드 테스트입니다.",
        help="Video description",
    )
    upload_parser.add_argument(
        "--private",
        action="store_true",
        help="Upload as private video",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Import here to avoid circular imports
    from src.agents.project_manager_agent import ProjectManagerAgent
    from src.database import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            agent = ProjectManagerAgent(db_session=session)

            if args.command == "status":
                result = await agent.run("status")
            elif args.command == "generate":
                result = await agent.run("generate", episode=args.episode, private=args.private)
            elif args.command == "history":
                result = await agent.run("history", limit=args.limit)
            elif args.command == "migrate":
                result = await agent.run(
                    "migrate",
                    action=args.action,
                    revision=args.revision,
                )
            elif args.command == "cleanup":
                result = await agent.run(
                    "cleanup",
                    older_than_days=args.days,
                    dry_run=not args.execute,
                )
            elif args.command == "init":
                result = await agent.run("init")
            elif args.command == "youtube-auth":
                # YouTube OAuth 인증
                from src.youtube_uploader import YouTubeUploader

                uploader = YouTubeUploader.__new__(YouTubeUploader)
                uploader.credentials = None
                uploader.youtube = None

                # 인증 URL 생성
                auth_url = uploader.get_auth_url()
                print("\n=== YouTube 인증 ===")
                print("아래 URL을 브라우저에서 열고 Google 계정으로 로그인하세요:")
                print(f"\n{auth_url}\n")
                print("인증 후 리다이렉트된 URL에서 'code=' 뒤의 값을 복사하세요.")
                code = input("인증 코드를 입력하세요: ").strip()

                if code:
                    tokens = uploader.exchange_code(code)
                    print("\n성공! 아래 refresh_token을 .env 파일에 저장하세요:")
                    print(f"\nYOUTUBE_REFRESH_TOKEN={tokens['refresh_token']}\n")
                return 0
            elif args.command == "upload-test":
                # Direct YouTube upload test (bypasses workflow)
                from pathlib import Path as P

                from src.youtube_uploader import YouTubeUploader

                video_path = P(args.video_path)
                if not video_path.exists():
                    print(f"Error: 영상 파일을 찾을 수 없습니다: {video_path}")
                    return 1

                print(f"YouTube 업로드 테스트 시작...")
                print(f"  파일: {video_path}")
                print(f"  제목: {args.title}")
                print(f"  공개 설정: {'비공개' if args.private else '공개'}")

                uploader = YouTubeUploader()
                privacy = "private" if args.private else "public"
                upload_result = await uploader.upload(
                    video_path=str(video_path),
                    title=args.title,
                    description=args.description,
                    tags=["테스트", "AI", "넝심이"],
                    privacy_status=privacy,
                    is_shorts=True,
                )

                print(f"\n업로드 성공!")
                print(f"  Video ID: {upload_result.video_id}")
                print(f"  URL: {upload_result.url}")
                return 0
            else:
                print(f"Unknown command: {args.command}")
                return 1

            # Print result
            print(f"\n{'=' * 50}")
            print(f"Command: {args.command}")
            print(f"Success: {result.success}")
            print(f"Message: {result.message}")
            if result.data:
                print("\nData:")
                print(json.dumps(result.data, indent=2, ensure_ascii=False, default=str))
            print(f"{'=' * 50}\n")

            return 0 if result.success else 1

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
