const GeminiStoryGenerator = require('./gemini-story-generator');
const Veo3VideoGenerator = require('./veo3-video-generator');
const YouTubeUploader = require('./youtube-uploader');
require('dotenv').config();

async function testGemini() {
  console.log('=== Gemini API 테스트 ===');
  try {
    const generator = new GeminiStoryGenerator();
    const story = await generator.generateStory(1);
    console.log('✅ Gemini API 테스트 성공');
    console.log('생성된 스토리 제목:', story.title);
    console.log('요리:', story.dish);
    console.log('요약:', story.summary);
    return true;
  } catch (error) {
    console.error('❌ Gemini API 테스트 실패:', error.message);
    return false;
  }
}

async function testVeo3() {
  console.log('\n=== Veo3 API 테스트 ===');
  try {
    const generator = new Veo3VideoGenerator();
    // 간단한 테스트 프롬프트
    const result = await generator.generateVideo(
      'A cute raccoon character cooking in a kitchen, animated style, high quality',
      { duration: 5 }
    );
    console.log('✅ Veo3 API 테스트 성공');
    console.log('결과:', result);
    return true;
  } catch (error) {
    console.error('❌ Veo3 API 테스트 실패:', error.message);
    console.log('⚠️  Veo3 API가 아직 공개되지 않았을 수 있습니다.');
    return false;
  }
}

async function testYouTube() {
  console.log('\n=== YouTube API 테스트 ===');
  try {
    const uploader = new YouTubeUploader();
    
    // 채널 정보 가져오기 테스트
    const channelInfo = await uploader.getChannelInfo();
    console.log('✅ YouTube API 테스트 성공');
    console.log('채널명:', channelInfo.snippet.title);
    console.log('채널 ID:', channelInfo.id);
    return true;
  } catch (error) {
    console.error('❌ YouTube API 테스트 실패:', error.message);
    if (error.message.includes('refresh_token')) {
      console.log('💡 YouTube 인증이 필요합니다. scripts/youtube-auth-helper.js를 실행하세요.');
    }
    return false;
  }
}

async function runAllTests() {
  console.log('API 연결 테스트를 시작합니다...\n');
  
  const results = {
    gemini: await testGemini(),
    veo3: await testVeo3(),
    youtube: await testYouTube()
  };
  
  console.log('\n=== 테스트 결과 요약 ===');
  console.log(`Gemini API: ${results.gemini ? '✅' : '❌'}`);
  console.log(`Veo3 API: ${results.veo3 ? '✅' : '❌'}`);
  console.log(`YouTube API: ${results.youtube ? '✅' : '❌'}`);
  
  const allPassed = Object.values(results).every(r => r);
  
  if (allPassed) {
    console.log('\n✅ 모든 API 테스트 통과!');
    process.exit(0);
  } else {
    console.log('\n⚠️  일부 API 테스트 실패. 설정을 확인하세요.');
    process.exit(1);
  }
}

if (require.main === module) {
  runAllTests();
}

module.exports = { testGemini, testVeo3, testYouTube, runAllTests };

