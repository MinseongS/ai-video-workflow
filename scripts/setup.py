#!/usr/bin/env python3
"""API 키 설정 위자드"""

import argparse
import os
import sys
from getpass import getpass
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def get_input(prompt: str, default: str = "", secret: bool = False) -> str:
    """사용자 입력 받기"""
    display = f"{prompt} [{default}]: " if default else f"{prompt}: "
    value = getpass(display) if secret else input(display)
    return value.strip() or default


def check_config() -> None:
    """현재 설정 확인"""
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")

    items = [
        ("GOOGLE_API_KEY", True),
        ("YOUTUBE_CLIENT_ID", False),
        ("YOUTUBE_CLIENT_SECRET", True),
        ("YOUTUBE_REFRESH_TOKEN", True),
        ("DB_PASSWORD", True),
    ]

    print("\n=== 현재 설정 ===\n")
    for key, is_secret in items:
        value = os.getenv(key, "")
        display = "***" if (is_secret and value) else (value or "(미설정)")
        status = "✓" if value else "✗"
        print(f"  {status} {key}: {display}")
    print()


def collect_config() -> dict:
    """대화형으로 설정 수집"""
    print("\n=== AI Video Workflow 설정 ===\n")
    print("API 키를 입력하세요. 기본값은 [대괄호] 안에 표시됩니다.\n")

    config = {}

    # Google API
    print("--- Google API (https://aistudio.google.com/app/apikey) ---")
    config["GOOGLE_API_KEY"] = get_input("Google API Key", secret=True)

    # YouTube API
    print("\n--- YouTube API (https://console.cloud.google.com/apis/credentials) ---")
    config["YOUTUBE_CLIENT_ID"] = get_input("Client ID")
    config["YOUTUBE_CLIENT_SECRET"] = get_input("Client Secret", secret=True)
    config["YOUTUBE_REFRESH_TOKEN"] = get_input("Refresh Token", secret=True)

    # Database
    print("\n--- PostgreSQL ---")
    config["DB_USER"] = get_input("DB User", "postgres")
    config["DB_PASSWORD"] = get_input("DB Password", secret=True)
    config["DB_HOST"] = get_input("DB Host", "localhost")
    config["DB_PORT"] = get_input("DB Port", "5432")
    config["DB_NAME"] = get_input("DB Name", "ai_video_workflow")

    return config


def generate_env(config: dict) -> None:
    """Generate .env file"""
    content = f"""# Google API (Gemini + Veo3)
GOOGLE_API_KEY={config.get("GOOGLE_API_KEY", "")}

# YouTube API
YOUTUBE_CLIENT_ID={config.get("YOUTUBE_CLIENT_ID", "")}
YOUTUBE_CLIENT_SECRET={config.get("YOUTUBE_CLIENT_SECRET", "")}
YOUTUBE_REFRESH_TOKEN={config.get("YOUTUBE_REFRESH_TOKEN", "")}

# PostgreSQL
DB_USER={config.get("DB_USER", "postgres")}
DB_PASSWORD={config.get("DB_PASSWORD", "")}
DB_HOST={config.get("DB_HOST", "localhost")}
DB_PORT={config.get("DB_PORT", "5432")}
DB_NAME={config.get("DB_NAME", "ai_video_workflow")}
"""
    path = PROJECT_ROOT / ".env"
    path.write_text(content)
    print(f"✓ {path} 생성됨")


def generate_k8s_secrets(config: dict) -> None:
    """Generate Kubernetes secrets"""
    content = f"""apiVersion: v1
kind: Secret
metadata:
  name: ai-video-secrets
type: Opaque
stringData:
  GOOGLE_API_KEY: "{config.get("GOOGLE_API_KEY", "")}"
  YOUTUBE_CLIENT_ID: "{config.get("YOUTUBE_CLIENT_ID", "")}"
  YOUTUBE_CLIENT_SECRET: "{config.get("YOUTUBE_CLIENT_SECRET", "")}"
  YOUTUBE_REFRESH_TOKEN: "{config.get("YOUTUBE_REFRESH_TOKEN", "")}"
  DB_PASSWORD: "{config.get("DB_PASSWORD", "")}"
"""
    path = PROJECT_ROOT / "k8s" / "secrets.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(content)
    print(f"✓ {path} 생성됨 (git에 커밋하지 마세요!)")


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Video Workflow 설정")
    parser.add_argument("--check", action="store_true", help="현재 설정 확인")
    args = parser.parse_args()

    if args.check:
        check_config()
        return 0

    config = collect_config()

    print("\n=== 설정 요약 ===")
    for key, value in config.items():
        display = (
            "***"
            if ("KEY" in key or "SECRET" in key or "TOKEN" in key or "PASSWORD" in key)
            else value
        )
        print(f"  {key}: {display or '(빈값)'}")

    if input("\n설정 파일을 생성하시겠습니까? [Y/n]: ").lower() == "n":
        print("취소됨")
        return 1

    generate_env(config)
    generate_k8s_secrets(config)

    print("\n=== 완료 ===")
    print("다음 단계: uv run python scripts/init_db.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
