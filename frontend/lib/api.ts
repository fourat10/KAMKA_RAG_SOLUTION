import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface UploadResponse {
  document_id: string;
  filename: string;
  chunk_count: number;
  cloudinary_url: string;
  uploaded_at: string;
}

export interface Citation {
  reference: string;
  filename: string;
  page: number | null;
  chunk_index: number | null;
  excerpt: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  used_retrieval: boolean;
  session_id: string;
}

export const apiService = {
  async uploadDocument(file: File, userId: string): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);

    const response = await apiClient.post<UploadResponse>('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  async chat(
    query: string,
    documentIds: string[],
    userId: string,
    sessionId: string
  ): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>('/api/chat', {
      query,
      document_ids: documentIds,
      user_id: userId,
      session_id: sessionId,
    });

    return response.data;
  },

  async chatStream(
    query: string,
    documentIds: string[],
    userId: string,
    sessionId: string,
    onToken: (token: string) => void,
    onCitations: (citations: Citation[]) => void
  ): Promise<void> {
    const baseURL = API_BASE;
    const response = await fetch(`${baseURL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        document_ids: documentIds,
        user_id: userId,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // Keep incomplete event in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            const jsonStr = trimmed.slice(6); // Remove 'data: ' prefix
            try {
              const event = JSON.parse(jsonStr);

              if (event.type === 'token') {
                onToken(event.content);
              } else if (event.type === 'citations') {
                onCitations(event.data);
              } else if (event.type === 'done') {
                // Stream finished
                return;
              } else if (event.type === 'error') {
                throw new Error(event.content);
              }
            } catch (e) {
              if (e instanceof SyntaxError) {
                console.error('Failed to parse SSE event:', jsonStr);
              } else {
                throw e;
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  async healthCheck(): Promise<boolean> {
    try {
      await apiClient.get('/health');
      return true;
    } catch {
      return false;
    }
  },
};
