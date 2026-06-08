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
    userId: string
  ): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>('/api/chat', {
      query,
      document_ids: documentIds,
      user_id: userId,
    });

    return response.data;
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
