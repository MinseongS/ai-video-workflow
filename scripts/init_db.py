"""데이터베이스 초기화 스크립트"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import close_db, init_db


async def main():
    """데이터베이스 초기화"""
    try:
        print("데이터베이스 초기화 중...")
        await init_db()
        print("✅ 데이터베이스 초기화 완료!")
    except Exception as error:
        print(f"❌ 데이터베이스 초기화 오류: {error}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
