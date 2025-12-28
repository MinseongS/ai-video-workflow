const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

class GeminiStoryGenerator {
  constructor() {
    this.apiKey = process.env.GEMINI_API_KEY;
    if (!this.apiKey) {
      throw new Error('GEMINI_API_KEY가 설정되지 않았습니다.');
    }
    this.genAI = new GoogleGenerativeAI(this.apiKey);
    this.model = this.genAI.getGenerativeModel({ model: 'gemini-1.5-pro' });
    
    // 캐릭터 정보
    this.mainCharacter = {
      name: process.env.MAIN_CHARACTER_NAME || '넝심이',
      description: process.env.MAIN_CHARACTER_DESCRIPTION || '살짝 너구리 같은 귀여운 라쿤 캐릭터, 요리를 좋아함'
    };
    
    this.supportingCharacter = {
      name: process.env.SUPPORTING_CHARACTER_NAME || '조연캐릭터',
      description: process.env.SUPPORTING_CHARACTER_DESCRIPTION || '넝심이의 친구, 항상 함께 등장하는 조연 캐릭터'
    };
    
    // 스토리 히스토리 (연속성 유지)
    this.storyHistory = [];
  }

  /**
   * 이전 스토리 히스토리를 로드합니다
   */
  loadStoryHistory(history) {
    this.storyHistory = history || [];
  }

  /**
   * 새로운 요리 영상 스토리를 생성합니다
   */
  async generateStory(episodeNumber = null) {
    const episode = episodeNumber || this.storyHistory.length + 1;
    
    const prompt = this.buildPrompt(episode);
    
    try {
      const result = await this.model.generateContent(prompt);
      const response = await result.response;
      const text = response.text();
      
      const storyData = this.parseStoryResponse(text, episode);
      
      // 히스토리에 추가
      this.storyHistory.push({
        episode,
        date: new Date().toISOString(),
        ...storyData
      });
      
      return storyData;
    } catch (error) {
      console.error('스토리 생성 중 오류:', error);
      throw error;
    }
  }

  /**
   * 프롬프트를 구성합니다
   */
  buildPrompt(episode) {
    const historyContext = this.storyHistory.length > 0
      ? `\n\n이전 에피소드 요약:\n${this.storyHistory.slice(-5).map(h => 
          `에피소드 ${h.episode}: ${h.title} - ${h.summary}`
        ).join('\n')}`
      : '';

    return `당신은 귀여운 라쿤 캐릭터 "넝심이"의 요리 쇼츠 영상을 위한 스토리를 작성하는 작가입니다.

캐릭터 정보:
- 주인공: ${this.mainCharacter.name} - ${this.mainCharacter.description}
- 조연: ${this.supportingCharacter.name} - ${this.supportingCharacter.description}

요구사항:
1. 요리 영상이 메인 콘텐츠입니다
2. 간단하고 귀여운 스토리가 요리 과정과 자연스럽게 연결됩니다
3. 캐릭터들은 일관성 있게 유지됩니다
4. 쇼츠 영상(60초 이내)에 적합한 분량입니다
5. 시청자들이 즐겁게 볼 수 있는 가벼운 톤입니다

${historyContext}

에피소드 ${episode}를 위한 스토리를 생성해주세요. 다음 JSON 형식으로 응답해주세요:

{
  "title": "영상 제목",
  "dish": "만들 요리 이름",
  "summary": "스토리 요약 (1-2문장)",
  "story": "상세 스토리 설명",
  "cooking_steps": ["요리 단계 1", "요리 단계 2", "요리 단계 3"],
  "video_prompts": [
    "영상 프롬프트 1 (Veo3용)",
    "영상 프롬프트 2 (Veo3용)",
    "영상 프롬프트 3 (Veo3용)"
  ],
  "tags": ["태그1", "태그2", "태그3"],
  "description": "YouTube 설명란용 텍스트"
}

스토리는 요리 과정과 자연스럽게 연결되어야 하며, ${this.mainCharacter.name}와 ${this.supportingCharacter.name}의 캐릭터가 일관되게 유지되어야 합니다.`;
  }

  /**
   * 응답을 파싱합니다
   */
  parseStoryResponse(text, episode) {
    try {
      // JSON 부분만 추출
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
      
      // JSON이 없으면 기본 구조로 반환
      return {
        title: `넝심이의 요리 - 에피소드 ${episode}`,
        dish: '특별한 요리',
        summary: text.substring(0, 100),
        story: text,
        cooking_steps: ['준비', '요리', '완성'],
        video_prompts: [
          `${this.mainCharacter.name}가 요리를 준비하는 모습`,
          `${this.mainCharacter.name}가 요리하는 모습`,
          `${this.mainCharacter.name}가 완성된 요리를 보여주는 모습`
        ],
        tags: ['요리', '라쿤', '쇼츠'],
        description: text
      };
    } catch (error) {
      console.error('응답 파싱 오류:', error);
      // 기본값 반환
      return {
        title: `넝심이의 요리 - 에피소드 ${episode}`,
        dish: '특별한 요리',
        summary: '넝심이가 요리를 만드는 귀여운 영상',
        story: text,
        cooking_steps: ['준비', '요리', '완성'],
        video_prompts: [
          `${this.mainCharacter.name}가 요리를 준비하는 모습`,
          `${this.mainCharacter.name}가 요리하는 모습`,
          `${this.mainCharacter.name}가 완성된 요리를 보여주는 모습`
        ],
        tags: ['요리', '라쿤', '쇼츠'],
        description: text
      };
    }
  }

  /**
   * 스토리 히스토리를 저장합니다
   */
  getStoryHistory() {
    return this.storyHistory;
  }
}

module.exports = GeminiStoryGenerator;

