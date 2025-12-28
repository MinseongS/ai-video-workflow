const GeminiStoryGenerator = require('./gemini-story-generator');
const Veo3VideoGenerator = require('./veo3-video-generator');
const YouTubeUploader = require('./youtube-uploader');
const fs = require('fs').promises;
const path = require('path');
require('dotenv').config();

class DailyVideoGenerator {
  constructor() {
    this.storyGenerator = new GeminiStoryGenerator();
    this.videoGenerator = new Veo3VideoGenerator();
    this.youtubeUploader = new YouTubeUploader();
    this.historyFile = path.join(__dirname, '../data/story-history.json');
  }

  /**
   * 스토리 히스토리 로드
   */
  async loadHistory() {
    try {
      const data = await fs.readFile(this.historyFile, 'utf-8');
      const history = JSON.parse(data);
      this.storyGenerator.loadStoryHistory(history);
      return history;
    } catch (error) {
      if (error.code === 'ENOENT') {
        // 파일이 없으면 빈 히스토리로 시작
        await this.ensureDataDir();
        return [];
      }
      throw error;
    }
  }

  /**
   * 스토리 히스토리 저장
   */
  async saveHistory() {
    await this.ensureDataDir();
    const history = this.storyGenerator.getStoryHistory();
    await fs.writeFile(
      this.historyFile,
      JSON.stringify(history, null, 2),
      'utf-8'
    );
  }

  /**
   * 데이터 디렉토리 생성
   */
  async ensureDataDir() {
    const dataDir = path.join(__dirname, '../data');
    try {
      await fs.mkdir(dataDir, { recursive: true });
    } catch (error) {
      console.error('데이터 디렉토리 생성 오류:', error);
    }
  }

  /**
   * 일일 영상 생성 및 업로드 프로세스
   */
  async generateAndUploadDailyVideo() {
    try {
      console.log('=== 일일 영상 생성 시작 ===');
      
      // 1. 히스토리 로드
      console.log('1. 스토리 히스토리 로드 중...');
      await this.loadHistory();
      
      // 2. 스토리 생성
      console.log('2. 새로운 스토리 생성 중...');
      const story = await this.storyGenerator.generateStory();
      console.log(`생성된 스토리: ${story.title}`);
      
      // 3. 영상 생성
      console.log('3. 영상 생성 중...');
      const videoPath = await this.videoGenerator.generateVideoSequence(
        story.video_prompts,
        {
          duration: 5, // 각 세그먼트 5초
          outputFilename: `video_${Date.now()}.mp4`
        }
      );
      console.log(`영상 생성 완료: ${videoPath}`);
      
      // 4. YouTube 업로드
      console.log('4. YouTube 업로드 중...');
      const uploadResult = await this.youtubeUploader.uploadShorts(
        videoPath,
        {
          title: story.title,
          description: story.description,
          tags: story.tags,
          privacyStatus: 'public'
        }
      );
      console.log(`업로드 완료: ${uploadResult.url}`);
      
      // 5. 히스토리 저장
      console.log('5. 히스토리 저장 중...');
      await this.saveHistory();
      
      // 6. 결과 반환
      return {
        success: true,
        story,
        videoPath,
        uploadResult,
        episode: this.storyGenerator.getStoryHistory().length
      };
    } catch (error) {
      console.error('일일 영상 생성 오류:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// CLI에서 직접 실행할 때
if (require.main === module) {
  const generator = new DailyVideoGenerator();
  generator.generateAndUploadDailyVideo()
    .then(result => {
      if (result.success) {
        console.log('\n✅ 성공적으로 완료되었습니다!');
        console.log(`에피소드: ${result.episode}`);
        console.log(`영상 URL: ${result.uploadResult.url}`);
        process.exit(0);
      } else {
        console.error('\n❌ 오류 발생:', result.error);
        process.exit(1);
      }
    })
    .catch(error => {
      console.error('치명적 오류:', error);
      process.exit(1);
    });
}

module.exports = DailyVideoGenerator;

