"""메인 실행 스크립트"""

import argparse
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database import AsyncSessionLocal, init_db
from src.workflow import VideoWorkflowAgent


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="AI Video Workflow")
    parser.add_argument("episode", type=int, nargs="?", help="Episode number")
    parser.add_argument(
        "--private", action="store_true", help="Upload as private video (for testing)"
    )
    args = parser.parse_args()

    db_session = None
    try:
        # 데이터베이스 초기화
        try:
            await init_db()
        except Exception as e:
            print(f"데이터베이스 초기화 경고: {e}")

        db_session = AsyncSessionLocal()

        # 워크플로우 실행
        agent = VideoWorkflowAgent(db_session=db_session)
        result = await agent.run(episode_number=args.episode, private=args.private)

        # LangGraph returns dict
        error = result.get("error") if isinstance(result, dict) else result.error
        if error:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n작업이 중단되었습니다.")
        sys.exit(130)
    except Exception as error:
        print(f"오류: {error}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        if db_session:
            await db_session.close()


if __name__ == "__main__":
    asyncio.run(main())
