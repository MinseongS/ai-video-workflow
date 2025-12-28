const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs').promises;
const path = require('path');

const execAsync = promisify(exec);

async function mergeVideos() {
  try {
    const segments = JSON.parse(process.env.SEGMENTS || '[]');
    const outputPath = process.env.OUTPUT_PATH || path.join(__dirname, '../output/videos/merged_video.mp4');

    if (segments.length === 0) {
      throw new Error('병합할 영상 세그먼트가 없습니다.');
    }

    // 출력 디렉토리 생성
    const outputDir = path.dirname(outputPath);
    await fs.mkdir(outputDir, { recursive: true });

    // 세그먼트 파일 다운로드 (필요한 경우)
    const segmentPaths = [];
    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i];
      let segmentPath;

      if (segment.videoUrl) {
        // URL에서 다운로드
        const axios = require('axios');
        const response = await axios.get(segment.videoUrl, {
          responseType: 'arraybuffer'
        });
        segmentPath = path.join(outputDir, `segment_${i + 1}.mp4`);
        await fs.writeFile(segmentPath, response.data);
      } else if (segment.filePath) {
        segmentPath = segment.filePath;
      } else {
        throw new Error(`세그먼트 ${i + 1}에 유효한 경로나 URL이 없습니다.`);
      }

      segmentPaths.push(segmentPath);
    }

    // ffmpeg를 사용하여 영상 합치기
    const fileListPath = path.join(outputDir, 'filelist.txt');
    const fileListContent = segmentPaths.map(p => `file '${p}'`).join('\n');
    await fs.writeFile(fileListPath, fileListContent);

    // 영상 합치기
    await execAsync(
      `ffmpeg -f concat -safe 0 -i "${fileListPath}" -c copy "${outputPath}"`
    );

    // 임시 파일 정리
    await fs.unlink(fileListPath);
    for (const segmentPath of segmentPaths) {
      if (segmentPath.startsWith(outputDir)) {
        try {
          await fs.unlink(segmentPath);
        } catch (error) {
          // 무시
        }
      }
    }

    console.log(`영상 합치기 완료: ${outputPath}`);
    process.exit(0);
  } catch (error) {
    console.error('영상 합치기 오류:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  mergeVideos();
}

module.exports = { mergeVideos };

