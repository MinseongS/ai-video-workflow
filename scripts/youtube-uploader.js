const { google } = require('googleapis');
const fs = require('fs').promises;
const path = require('path');
require('dotenv').config();

class YouTubeUploader {
  constructor() {
    this.clientId = process.env.YOUTUBE_CLIENT_ID;
    this.clientSecret = process.env.YOUTUBE_CLIENT_SECRET;
    this.redirectUri = process.env.YOUTUBE_REDIRECT_URI;
    this.refreshToken = process.env.YOUTUBE_REFRESH_TOKEN;
    this.channelId = process.env.YOUTUBE_CHANNEL_ID;
    
    this.oauth2Client = new google.auth.OAuth2(
      this.clientId,
      this.clientSecret,
      this.redirectUri
    );

    if (this.refreshToken) {
      this.oauth2Client.setCredentials({
        refresh_token: this.refreshToken
      });
    }

    this.youtube = google.youtube({
      version: 'v3',
      auth: this.oauth2Client
    });
  }

  /**
   * OAuth 인증 URL 생성
   */
  getAuthUrl() {
    const scopes = [
      'https://www.googleapis.com/auth/youtube.upload',
      'https://www.googleapis.com/auth/youtube'
    ];

    return this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: scopes,
      prompt: 'consent'
    });
  }

  /**
   * 인증 코드로 토큰 교환
   */
  async getTokensFromCode(code) {
    const { tokens } = await this.oauth2Client.getToken(code);
    this.oauth2Client.setCredentials(tokens);
    return tokens;
  }

  /**
   * 영상을 YouTube에 업로드합니다
   */
  async uploadVideo(videoPath, metadata) {
    const {
      title,
      description,
      tags = [],
      categoryId = '24', // 엔터테인먼트
      privacyStatus = 'public',
      defaultLanguage = 'ko',
      defaultAudioLanguage = 'ko'
    } = metadata;

    try {
      // 파일 크기 확인
      const stats = await fs.stat(videoPath);
      const fileSize = stats.size;

      // YouTube API를 사용한 업로드
      const response = await this.youtube.videos.insert({
        part: 'snippet,status',
        requestBody: {
          snippet: {
            title: title,
            description: description,
            tags: tags,
            categoryId: categoryId,
            defaultLanguage: defaultLanguage,
            defaultAudioLanguage: defaultAudioLanguage
          },
          status: {
            privacyStatus: privacyStatus,
            selfDeclaredMadeForKids: false
          }
        },
        media: {
          body: require('fs').createReadStream(videoPath)
        }
      }, {
        // 대용량 파일 업로드를 위한 설정
        onUploadProgress: (evt) => {
          const progress = (evt.bytesRead / fileSize) * 100;
          console.log(`업로드 진행률: ${progress.toFixed(2)}%`);
        }
      });

      console.log('영상 업로드 완료:', response.data.id);
      return {
        videoId: response.data.id,
        url: `https://www.youtube.com/watch?v=${response.data.id}`,
        title: response.data.snippet.title
      };
    } catch (error) {
      console.error('YouTube 업로드 오류:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * 쇼츠로 업로드 (Shorts는 특별한 태그나 설정이 필요할 수 있음)
   */
  async uploadShorts(videoPath, metadata) {
    // 쇼츠는 일반 영상과 동일하게 업로드하되, 제목이나 태그에 #Shorts 추가
    const shortsMetadata = {
      ...metadata,
      title: metadata.title + ' #Shorts',
      tags: [...(metadata.tags || []), 'Shorts', '쇼츠', '요리', '라쿤', '넝심이']
    };

    return await this.uploadVideo(videoPath, shortsMetadata);
  }

  /**
   * 업로드된 영상 정보 가져오기
   */
  async getVideoInfo(videoId) {
    try {
      const response = await this.youtube.videos.list({
        part: 'snippet,statistics',
        id: videoId
      });

      return response.data.items[0];
    } catch (error) {
      console.error('영상 정보 가져오기 오류:', error);
      throw error;
    }
  }

  /**
   * 채널 정보 가져오기
   */
  async getChannelInfo() {
    try {
      const response = await this.youtube.channels.list({
        part: 'snippet,statistics',
        mine: true
      });

      return response.data.items[0];
    } catch (error) {
      console.error('채널 정보 가져오기 오류:', error);
      throw error;
    }
  }
}

module.exports = YouTubeUploader;

