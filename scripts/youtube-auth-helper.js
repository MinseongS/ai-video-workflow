const YouTubeUploader = require('./youtube-uploader');
const readline = require('readline');
require('dotenv').config();

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(query) {
  return new Promise(resolve => rl.question(query, resolve));
}

async function main() {
  console.log('=== YouTube API 인증 도우미 ===\n');
  
  const uploader = new YouTubeUploader();
  
  // 인증 URL 생성
  const authUrl = uploader.getAuthUrl();
  console.log('다음 URL을 브라우저에서 열어주세요:');
  console.log(authUrl);
  console.log('\n인증 후 리다이렉트된 URL에서 "code=" 뒤의 인증 코드를 복사하세요.\n');
  
  // 인증 코드 입력 받기
  const code = await question('인증 코드를 입력하세요: ');
  
  try {
    // 토큰 교환
    console.log('\n토큰을 교환하는 중...');
    const tokens = await uploader.getTokensFromCode(code.trim());
    
    console.log('\n✅ 인증 성공!');
    console.log('\n다음 토큰을 .env 파일에 추가하세요:');
    console.log(`YOUTUBE_REFRESH_TOKEN=${tokens.refresh_token}`);
    
    if (tokens.access_token) {
      console.log(`YOUTUBE_ACCESS_TOKEN=${tokens.access_token}`);
    }
    
    // 채널 정보 가져오기
    try {
      const channelInfo = await uploader.getChannelInfo();
      console.log(`\n채널 정보:`);
      console.log(`- 채널명: ${channelInfo.snippet.title}`);
      console.log(`- 채널 ID: ${channelInfo.id}`);
      console.log(`\n.env 파일에 다음도 추가하세요:`);
      console.log(`YOUTUBE_CHANNEL_ID=${channelInfo.id}`);
    } catch (error) {
      console.log('\n⚠️  채널 정보를 가져올 수 없습니다. 수동으로 설정하세요.');
    }
    
  } catch (error) {
    console.error('\n❌ 인증 실패:', error.message);
    if (error.response) {
      console.error('상세 오류:', error.response.data);
    }
  }
  
  rl.close();
}

if (require.main === module) {
  main().catch(error => {
    console.error('오류 발생:', error);
    process.exit(1);
  });
}

module.exports = { main };

