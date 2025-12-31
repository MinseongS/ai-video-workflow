"""LangGraph 기반 워크플로우 에이전트"""

import json
from datetime import datetime
from typing import Literal

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.story_agent import StoryAgent
from src.agents.video_agent import VideoAgent
from src.agents.youtube_agent import YouTubeAgent
from src.config import settings
from src.database import AsyncSessionLocal
from src.models import StoryHistoryEntry, WorkflowState
from src.repository import WorkflowExecutionRepository


class VideoWorkflowAgent:
    """LangGraph 기반 영상 생성 워크플로우 에이전트"""

    def __init__(self, db_session: AsyncSession | None = None):
        self.history_file = settings.data_dir / "story-history.json"

        # 데이터베이스 세션 (없으면 자동 생성)
        self.db_session = db_session
        self._use_db = db_session is not None

        # 에이전트 초기화
        self.story_agent = StoryAgent(db_session=db_session)
        self.video_agent = VideoAgent(db_session=db_session)
        self.youtube_agent = YouTubeAgent(db_session=db_session)

        # 워크플로우 그래프 구성
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """LangGraph 워크플로우 그래프 구성"""
        workflow = StateGraph(WorkflowState)

        # 노드 추가 (모두 비동기)
        workflow.add_node("load_history", self.load_history_node)
        workflow.add_node("generate_story", self.generate_story_node)
        workflow.add_node("generate_videos", self.generate_videos_node)
        workflow.add_node("upload_to_youtube", self.upload_to_youtube_node)
        workflow.add_node("save_history", self.save_history_node)
        workflow.add_node("handle_error", self.handle_error_node)

        # 엣지 추가
        workflow.set_entry_point("load_history")
        workflow.add_edge("load_history", "generate_story")
        workflow.add_conditional_edges(
            "generate_story",
            self.should_continue_after_story,
            {"continue": "generate_videos", "error": "handle_error"},
        )
        workflow.add_conditional_edges(
            "generate_videos",
            self.should_continue_after_videos,
            {"continue": "upload_to_youtube", "error": "handle_error"},
        )
        workflow.add_conditional_edges(
            "upload_to_youtube",
            self.should_continue_after_upload,
            {"continue": "save_history", "error": "handle_error"},
        )
        workflow.add_edge("save_history", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    async def load_history_node(self, state: WorkflowState) -> WorkflowState:
        """스토리 히스토리 로드"""
        print("1. 스토리 히스토리 로드 중...")
        try:
            if self._use_db and self.db_session:
                # StoryAgent를 사용하여 히스토리 로드
                history = await self.story_agent.get_history()
                state.story_history = history
            else:
                # 파일에서 로드 (기존 방식, 호환성 유지)
                if self.history_file.exists():
                    history_data = json.loads(self.history_file.read_text())
                    history = [
                        StoryHistoryEntry(**entry) if isinstance(entry, dict) else entry
                        for entry in history_data
                    ]
                    state.story_history = history
                else:
                    state.story_history = []
        except Exception as error:
            print(f"히스토리 로드 오류: {error}")
            state.story_history = []

        state.current_step = "load_history"
        return state

    async def generate_story_node(self, state: WorkflowState) -> WorkflowState:
        """스토리 생성 (StoryAgent 사용)"""
        print("2. 새로운 스토리 생성 중...")
        try:
            episode = state.episode_number or len(state.story_history) + 1

            # StoryAgent 실행
            result = await self.story_agent.run(
                episode=episode,
                save_to_db=self._use_db,
            )

            if not result.success or not result.story:
                raise ValueError(result.error or "스토리 생성 실패")

            state.story = result.story
            state.story_id = result.story_id
            state.current_step = "generate_story"
            print(f"생성된 스토리: {result.story.title}")

        except Exception as error:
            print(f"스토리 생성 오류: {error}")
            state.error = str(error)
            state.current_step = "error"

        return state

    async def generate_videos_node(self, state: WorkflowState) -> WorkflowState:
        """영상 생성 (VideoAgent 사용)"""
        print("3. 영상 생성 중...")
        try:
            if not state.story:
                raise ValueError("스토리가 생성되지 않았습니다.")

            # Veo3 영상 생성 스킵 옵션 확인
            if settings.skip_video_generation:
                if not settings.test_video_path:
                    raise ValueError(
                        "skip_video_generation=True이지만 test_video_path가 설정되지 않았습니다."
                    )
                print(f"[스킵] Veo3 영상 생성 스킵, 테스트 영상 사용: {settings.test_video_path}")
                state.final_video_path = settings.test_video_path
                state.video_generation_id = None
                state.current_step = "generate_videos"
                return state

            output_filename = f"video_{int(datetime.now().timestamp())}.mp4"

            # VideoAgent 실행
            result = await self.video_agent.run(
                prompts=state.story.video_prompts,
                story_id=state.story_id,
                duration=5,
                output_filename=output_filename,
            )

            if not result.success or not result.video_path:
                raise ValueError(result.error or "영상 생성 실패")

            state.final_video_path = result.video_path
            state.video_generation_id = result.video_generation_id
            state.current_step = "generate_videos"
            print(f"영상 생성 완료: {result.video_path}")

        except Exception as error:
            print(f"영상 생성 오류: {error}")
            state.error = str(error)
            state.current_step = "error"

        return state

    async def upload_to_youtube_node(self, state: WorkflowState) -> WorkflowState:
        """YouTube 업로드 (YouTubeAgent 사용)"""
        print("4. YouTube 업로드 중...")
        try:
            if not state.story or not state.final_video_path:
                raise ValueError("스토리나 영상 경로가 없습니다.")

            # YouTubeAgent 실행
            result = await self.youtube_agent.run(
                video_path=state.final_video_path,
                title=state.story.title,
                description=state.story.description,
                tags=state.story.tags,
                privacy_status=state.privacy_status,
                story_id=state.story_id,
                video_generation_id=state.video_generation_id,
            )

            if not result.success:
                raise ValueError(result.error or "YouTube 업로드 실패")

            # YouTubeUploadResult 호환을 위한 간단한 객체 생성
            from src.models import YouTubeUploadResult

            state.upload_result = YouTubeUploadResult(
                video_id=result.video_id or "",
                url=result.video_url or "",
                title=state.story.title,
            )
            state.youtube_upload_id = result.upload_record_id
            state.current_step = "upload_to_youtube"
            print(f"업로드 완료: {result.video_url}")

        except Exception as error:
            print(f"YouTube 업로드 오류: {error}")
            state.error = str(error)
            state.current_step = "error"

        return state

    async def save_history_node(self, state: WorkflowState) -> WorkflowState:
        """히스토리 저장"""
        print("5. 히스토리 저장 중...")
        try:
            if self._use_db and self.db_session:
                # 데이터베이스는 이미 저장되어 있으므로 커밋만
                await self.db_session.commit()
                # 히스토리 다시 로드
                history = await self.story_agent.get_history(limit=100)
                state.story_history = history
            else:
                # 파일에 저장 (기존 방식, 호환성 유지)
                history = list(state.story_history)
                if state.story:
                    new_entry = StoryHistoryEntry(
                        episode=state.story.episode,
                        date=state.story.date,
                        title=state.story.title,
                        dish=state.story.dish,
                        summary=state.story.summary,
                        story=state.story.story,
                        cooking_steps=state.story.cooking_steps,
                        video_prompts=state.story.video_prompts,
                        tags=state.story.tags,
                        description=state.story.description,
                    )
                    history.append(new_entry)

                history_data = [
                    entry.model_dump() if hasattr(entry, "model_dump") else entry
                    for entry in history
                ]
                self.history_file.write_text(json.dumps(history_data, ensure_ascii=False, indent=2))
                state.story_history = history

            state.current_step = "save_history"
        except Exception as error:
            print(f"히스토리 저장 오류: {error}")
            state.error = str(error)
            if self._use_db and self.db_session:
                await self.db_session.rollback()

        return state

    def handle_error_node(self, state: WorkflowState) -> WorkflowState:
        """에러 처리"""
        print(f"에러 발생: {state.error}")
        state.current_step = "error"
        return state

    def should_continue_after_story(self, state: WorkflowState) -> Literal["continue", "error"]:
        """스토리 생성 후 계속 진행 여부"""
        if state.error or not state.story:
            return "error"
        return "continue"

    def should_continue_after_videos(self, state: WorkflowState) -> Literal["continue", "error"]:
        """영상 생성 후 계속 진행 여부"""
        if state.error or not state.final_video_path:
            return "error"
        return "continue"

    def should_continue_after_upload(self, state: WorkflowState) -> Literal["continue", "error"]:
        """업로드 후 계속 진행 여부"""
        if state.error or not state.upload_result:
            return "error"
        return "continue"

    async def run(
        self, episode_number: int | None = None, private: bool = False
    ) -> WorkflowState:
        """워크플로우 실행"""
        print("=== 일일 영상 생성 시작 ===")

        # 데이터베이스 세션이 없으면 생성
        session = self.db_session
        if not session:
            session = AsyncSessionLocal()
            self.db_session = session
            self._use_db = True

            # 에이전트에도 세션 설정
            self.story_agent = StoryAgent(db_session=session)
            self.video_agent = VideoAgent(db_session=session)
            self.youtube_agent = YouTubeAgent(db_session=session)

        try:
            # 워크플로우 실행 기록 생성
            execution_id = None
            if self._use_db:
                exec_repo = WorkflowExecutionRepository(session)
                db_execution = await exec_repo.create(episode_number, "running")
                execution_id = db_execution.id
                await session.commit()

            privacy_status = "private" if private else "public"
            initial_state = WorkflowState(
                episode_number=episode_number,
                privacy_status=privacy_status,
                timestamp=datetime.now().isoformat(),
                execution_id=execution_id,
            )

            # LangGraph 실행
            final_state = await self.graph.ainvoke(initial_state)

            # 워크플로우 실행 기록 업데이트
            # LangGraph returns dict, not object
            error = final_state.get("error") if isinstance(final_state, dict) else final_state.error
            if self._use_db and execution_id:
                exec_repo = WorkflowExecutionRepository(session)
                status = "completed" if not error else "failed"
                story_id = final_state.get("story_id") if isinstance(final_state, dict) else final_state.story_id
                video_gen_id = final_state.get("video_generation_id") if isinstance(final_state, dict) else final_state.video_generation_id
                yt_upload_id = final_state.get("youtube_upload_id") if isinstance(final_state, dict) else final_state.youtube_upload_id
                await exec_repo.update(
                    execution_id,
                    status=status,
                    story_id=story_id,
                    video_generation_id=video_gen_id,
                    youtube_upload_id=yt_upload_id,
                    error_message=error,
                )
                await session.commit()

            if error:
                print(f"\n오류 발생: {error}")
            else:
                print("\n성공적으로 완료되었습니다!")
                upload_result = final_state.get("upload_result") if isinstance(final_state, dict) else final_state.upload_result
                story_history = final_state.get("story_history", []) if isinstance(final_state, dict) else final_state.story_history
                if upload_result:
                    print(f"에피소드: {len(story_history)}")
                    print(f"영상 URL: {upload_result.url if hasattr(upload_result, 'url') else upload_result.get('url')}")

            return final_state
        except Exception as error:
            print(f"워크플로우 실행 오류: {error}")
            if self._use_db and execution_id:
                exec_repo = WorkflowExecutionRepository(session)
                await exec_repo.update(execution_id, status="failed", error_message=str(error))
                await session.commit()
            raise
        finally:
            # 세션을 직접 생성한 경우에만 닫기
            if session and not self.db_session:
                await session.close()
