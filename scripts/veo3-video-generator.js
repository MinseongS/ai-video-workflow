const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');
require('dotenv').config();

class Veo3VideoGenerator {
  constructor() {
    this.apiKey = process.env.VEO3_API_KEY;
    this.projectId = process.env.VEO3_PROJECT_ID;
    
    if (!this.apiKey || !this.projectId) {
      throw new Error('VEO3_API_KEY와 VEO3_PROJECT_ID가 설정되지 않았습니다.');
    }
    
    // Veo3 API 엔드포인트 (실제 API가 공개되면 업데이트 필요)
    this.baseUrl = 'https://veo3.googleapis.com/v1';
    this.outputDir = path.join(__dirname, '../output/videos');
    
    // 출력 디렉토리 생성
    this.ensureOutputDir();
  }

  async ensureOutputDir() {
    try {
      await fs.mkdir(this.outputDir, { recursive: true });
    } catch (error) {
      console.error('출력 디렉토리 생성 오류:', error);
    }
  }

  /**
   * Veo3 API를 사용하여 영상을 생성합니다
   */
  async generateVideo(prompt, options = {}) {
    const {
      duration = 5, // 초 단위
      aspectRatio = '9:16', // 쇼츠용 세로 비율
      style = 'cute, animated, raccoon cooking',
      negativePrompt = 'realistic, human, scary'
    } = options;

    const fullPrompt = `${prompt}, ${style}, high quality, cute raccoon character, cooking video, shorts format, ${aspectRatio} aspect ratio, ${negativePrompt ? `avoid: ${negativePrompt}` : ''}`;

    try {
      // Veo3 API 호출 (실제 API 스펙에 맞게 수정 필요)
      const response = await axios.post(
        `${this.baseUrl}/projects/${this.projectId}/videos:generate`,
        {
          prompt: fullPrompt,
          duration: duration,
          aspectRatio: aspectRatio,
          model: 'veo-3'
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // 비동기 작업이므로 작업 ID를 반환
      if (response.data.operation) {
        return {
          operationId: response.data.operation.name,
          status: 'processing'
        };
      }

      // 동기 응답인 경우
      if (response.data.videoUrl) {
        return {
          videoUrl: response.data.videoUrl,
          status: 'completed'
        };
      }

      throw new Error('예상치 못한 API 응답 형식');
    } catch (error) {
      console.error('Veo3 영상 생성 오류:', error.response?.data || error.message);
      
      // API가 아직 공개되지 않았을 경우를 대비한 모의 응답
      if (error.response?.status === 404 || error.code === 'ENOTFOUND') {
        console.warn('Veo3 API가 아직 사용 가능하지 않습니다. 모의 응답을 반환합니다.');
        return this.generateMockVideo(prompt, options);
      }
      
      throw error;
    }
  }

  /**
   * 작업 상태를 확인합니다
   */
  async checkOperationStatus(operationId) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/operations/${operationId}`,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          }
        }
      );

      return response.data;
    } catch (error) {
      console.error('작업 상태 확인 오류:', error);
      throw error;
    }
  }

  /**
   * 영상 다운로드
   */
  async downloadVideo(videoUrl, filename) {
    try {
      const response = await axios.get(videoUrl, {
        responseType: 'arraybuffer'
      });

      const filepath = path.join(this.outputDir, filename);
      await fs.writeFile(filepath, response.data);

      return filepath;
    } catch (error) {
      console.error('영상 다운로드 오류:', error);
      throw error;
    }
  }

  /**
   * 여러 프롬프트로 영상을 생성하고 합칩니다
   */
  async generateVideoSequence(prompts, options = {}) {
    const videos = [];
    
    for (let i = 0; i < prompts.length; i++) {
      console.log(`영상 ${i + 1}/${prompts.length} 생성 중...`);
      
      const result = await this.generateVideo(prompts[i], {
        ...options,
        duration: options.duration || 5
      });

      // 작업이 비동기인 경우 완료될 때까지 대기
      if (result.status === 'processing') {
        let operation = await this.checkOperationStatus(result.operationId);
        let attempts = 0;
        const maxAttempts = 60; // 최대 5분 대기

        while (operation.done === false && attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 5000)); // 5초 대기
          operation = await this.checkOperationStatus(result.operationId);
          attempts++;
        }

        if (operation.done && operation.response?.videoUrl) {
          const filepath = await this.downloadVideo(
            operation.response.videoUrl,
            `video_segment_${i + 1}.mp4`
          );
          videos.push(filepath);
        }
      } else if (result.videoUrl) {
        const filepath = await this.downloadVideo(
          result.videoUrl,
          `video_segment_${i + 1}.mp4`
        );
        videos.push(filepath);
      }
    }

    // 영상 합치기 (ffmpeg 사용)
    if (videos.length > 1) {
      return await this.mergeVideos(videos, options.outputFilename);
    }

    return videos[0];
  }

  /**
   * 여러 영상을 하나로 합칩니다 (ffmpeg 필요)
   */
  async mergeVideos(videoPaths, outputFilename = 'final_video.mp4') {
    const { exec } = require('child_process');
    const { promisify } = require('util');
    const execAsync = promisify(exec);

    const outputPath = path.join(this.outputDir, outputFilename);
    
    // ffmpeg를 사용하여 영상 합치기
    const fileListPath = path.join(this.outputDir, 'filelist.txt');
    const fileListContent = videoPaths.map(p => `file '${p}'`).join('\n');
    await fs.writeFile(fileListPath, fileListContent);

    try {
      await execAsync(
        `ffmpeg -f concat -safe 0 -i "${fileListPath}" -c copy "${outputPath}"`
      );
      
      // 임시 파일 정리
      await fs.unlink(fileListPath);
      
      return outputPath;
    } catch (error) {
      console.error('영상 합치기 오류:', error);
      throw error;
    }
  }

  /**
   * 모의 영상 생성 (API가 사용 불가능할 때)
   */
  async generateMockVideo(prompt, options) {
    console.log(`[모의] 영상 생성: ${prompt}`);
    
    // 실제로는 빈 영상 파일을 생성하거나, 테스트용 영상을 생성
    const filename = `mock_video_${Date.now()}.mp4`;
    const filepath = path.join(this.outputDir, filename);
    
    // 실제 구현에서는 실제 Veo3 API를 사용해야 합니다
    // 여기서는 파일 경로만 반환
    return {
      videoUrl: filepath,
      status: 'completed',
      mock: true
    };
  }
}

module.exports = Veo3VideoGenerator;

