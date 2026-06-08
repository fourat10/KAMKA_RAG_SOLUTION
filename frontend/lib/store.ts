import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Document {
  document_id: string;
  filename: string;
  chunk_count: number;
  cloudinary_url: string;
  uploaded_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Array<{
    reference: string;
    filename: string;
    page: number | null;
    chunk_index: number | null;
    excerpt: string;
  }>;
  timestamp: string;
}

interface AppStore {
  userId: string;
  setUserId: (userId: string) => void;
  documents: Document[];
  setDocuments: (documents: Document[]) => void;
  addDocument: (doc: Document) => void;
  removeDocument: (docId: string) => void;
  selectedDocIds: string[];
  setSelectedDocIds: (ids: string[]) => void;
  toggleDocumentSelection: (docId: string) => void;
  messages: ChatMessage[];
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  clearDocuments: () => void;
}

export const useAppStore = create<AppStore>()(
  persist(
    (set, get) => ({
      userId: '',
      setUserId: (userId) => {
        const currentUserId = get().userId;
        // If userId changed, clear documents and selections
        if (currentUserId && currentUserId !== userId) {
          set({
            userId,
            documents: [],
            selectedDocIds: [],
            messages: [],
          });
        } else {
          set({ userId });
        }
      },

      documents: [],
      setDocuments: (documents) => set({ documents }),
      addDocument: (doc) => set((state) => ({ documents: [...state.documents, doc] })),
      removeDocument: (docId) =>
        set((state) => ({
          documents: state.documents.filter((d) => d.document_id !== docId),
          selectedDocIds: state.selectedDocIds.filter((id) => id !== docId),
        })),

      selectedDocIds: [],
      setSelectedDocIds: (ids) => set({ selectedDocIds: ids }),
      toggleDocumentSelection: (docId) =>
        set((state) => {
          const ids = state.selectedDocIds.includes(docId)
            ? state.selectedDocIds.filter((id) => id !== docId)
            : [...state.selectedDocIds, docId];
          return { selectedDocIds: ids };
        }),

      messages: [],
      addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
      clearMessages: () => set({ messages: [] }),

      isLoading: false,
      setIsLoading: (loading) => set({ isLoading: loading }),

      error: null,
      setError: (error) => set({ error }),

      clearDocuments: () =>
        set({ documents: [], selectedDocIds: [], messages: [] }),
    }),
    {
      name: 'app-store',
      partialize: (state) => ({
        userId: state.userId,
        documents: state.documents,
        selectedDocIds: state.selectedDocIds,
        messages: state.messages,
      }),
    }
  )
);
