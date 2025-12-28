const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');
require('dotenv').config();

/**
 * n8n 워크플로우 설정 스크립트
 * 
 * 이 스크립트는 n8n API를 사용하여 워크플로우를 생성하거나 업데이트합니다.
 * 
 * 사용법:
 *   node scripts/setup-n8n-workflow.js [workflow-id]
 * 
 * workflow-id를 제공하지 않으면 새 워크플로우를 생성합니다.
 */

const N8N_BASE_URL = process.env.N8N_BASE_URL || 'http://localhost:5678';
const N8N_API_KEY = process.env.N8N_API_KEY;

class N8NWorkflowSetup {
  constructor() {
    this.baseUrl = N8N_BASE_URL;
    this.apiKey = N8N_API_KEY;
    
    if (!this.apiKey) {
      console.warn('⚠️  N8N_API_KEY가 설정되지 않았습니다.');
      console.warn('   n8n 설정에서 API 키를 생성하고 .env 파일에 추가하세요.');
      console.warn('   또는 n8n 웹 인터페이스에서 수동으로 워크플로우를 가져올 수 있습니다.');
    }
  }

  /**
   * n8n API 요청 헤더 생성
   */
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json'
    };
    
    if (this.apiKey) {
      headers['X-N8N-API-KEY'] = this.apiKey;
    }
    
    return headers;
  }

  /**
   * 워크플로우 파일 로드
   */
  async loadWorkflowFile(filename = 'daily-youtube-shorts-simple.json') {
    const filePath = path.join(__dirname, '../workflows', filename);
    const content = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(content);
  }

  /**
   * 기존 워크플로우 가져오기
   */
  async getWorkflow(workflowId) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/v1/workflows/${workflowId}`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('n8n API 인증 실패. N8N_API_KEY를 확인하세요.');
      }
      throw error;
    }
  }

  /**
   * 워크플로우 생성
   */
  async createWorkflow(workflowData) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/api/v1/workflows`,
        workflowData,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('n8n API 인증 실패. N8N_API_KEY를 확인하세요.');
      }
      throw error;
    }
  }

  /**
   * 워크플로우 업데이트
   */
  async updateWorkflow(workflowId, workflowData) {
    try {
      const response = await axios.put(
        `${this.baseUrl}/api/v1/workflows/${workflowId}`,
        workflowData,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('n8n API 인증 실패. N8N_API_KEY를 확인하세요.');
      }
      throw error;
    }
  }

  /**
   * 워크플로우 활성화
   */
  async activateWorkflow(workflowId, active = true) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/api/v1/workflows/${workflowId}/activate`,
        { active },
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('n8n API 인증 실패. N8N_API_KEY를 확인하세요.');
      }
      throw error;
    }
  }

  /**
   * 워크플로우 설정
   */
  async setupWorkflow(workflowId = null, filename = 'daily-youtube-shorts-simple.json') {
    console.log('=== n8n 워크플로우 설정 ===\n');
    
    // 워크플로우 파일 로드
    console.log(`워크플로우 파일 로드 중: ${filename}`);
    const workflowData = await this.loadWorkflowFile(filename);
    
    // 프로젝트 경로 설정
    const projectPath = process.env.PROJECT_PATH || '/Users/minseong/project/ai-youtube';
    
    // 워크플로우 노드에서 프로젝트 경로 업데이트
    if (workflowData.nodes) {
      workflowData.nodes.forEach(node => {
        if (node.parameters?.arguments) {
          node.parameters.arguments = node.parameters.arguments.replace(
            /\/Users\/minseong\/project\/ai-youtube/g,
            projectPath
          );
        }
      });
    }
    
    let result;
    
    if (workflowId) {
      // 기존 워크플로우 업데이트
      console.log(`기존 워크플로우 업데이트 중: ${workflowId}`);
      workflowData.id = workflowId;
      result = await this.updateWorkflow(workflowId, workflowData);
      console.log('✅ 워크플로우 업데이트 완료');
    } else {
      // 새 워크플로우 생성
      console.log('새 워크플로우 생성 중...');
      result = await this.createWorkflow(workflowData);
      console.log('✅ 워크플로우 생성 완료');
      workflowId = result.id;
    }
    
    console.log(`\n워크플로우 ID: ${workflowId}`);
    console.log(`워크플로우 URL: ${this.baseUrl}/workflow/${workflowId}`);
    
    // 워크플로우 활성화
    console.log('\n워크플로우 활성화 중...');
    await this.activateWorkflow(workflowId, true);
    console.log('✅ 워크플로우 활성화 완료');
    
    return {
      workflowId,
      url: `${this.baseUrl}/workflow/${workflowId}`,
      data: result
    };
  }
}

// CLI에서 직접 실행할 때
if (require.main === module) {
  const setup = new N8NWorkflowSetup();
  const workflowId = process.argv[2] || null;
  const filename = process.argv[3] || 'daily-youtube-shorts-simple.json';
  
  setup.setupWorkflow(workflowId, filename)
    .then(result => {
      console.log('\n✅ 설정 완료!');
      console.log(`\n다음 URL에서 워크플로우를 확인하세요:`);
      console.log(result.url);
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ 오류 발생:', error.message);
      if (!setup.apiKey) {
        console.error('\n💡 해결 방법:');
        console.error('1. n8n 웹 인터페이스에서 Settings > API로 이동');
        console.error('2. API 키 생성');
        console.error('3. .env 파일에 N8N_API_KEY 추가');
        console.error('\n또는 n8n 웹 인터페이스에서 수동으로 워크플로우를 가져올 수 있습니다:');
        console.error('1. Workflows > Import from File');
        console.error(`2. workflows/${filename} 파일 선택`);
      }
      process.exit(1);
    });
}

module.exports = N8NWorkflowSetup;

