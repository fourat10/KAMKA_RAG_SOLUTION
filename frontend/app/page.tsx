"use client";

import { useEffect } from "react";
import { useAppStore } from "@/lib/store";
import { generateUserId } from "@/lib/utils";
import { UploadForm } from "@/components/UploadForm";
import { DocumentList } from "@/components/DocumentList";
import { ChatInterface } from "@/components/ChatInterface";
import { UserIdCard } from "@/components/UserIdCard";

export default function Home() {
  const userId = useAppStore((state) => state.userId);
  const setUserId = useAppStore((state) => state.setUserId);
  const error = useAppStore((state) => state.error);
  const setError = useAppStore((state) => state.setError);

  useEffect(() => {
    if (!userId) {
      setUserId(generateUserId());
    }
  }, [userId, setUserId]);

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <h1 className="text-4xl font-bold text-gray-900">📚 Kamka</h1>
          <p className="text-gray-600 mt-2">
            Upload documents and chat with AI to find answers
          </p>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Global Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex justify-between items-center">
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-red-500 hover:text-red-700 font-bold text-lg"
            >
              ✕
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Upload & Documents */}
          <div className="lg:col-span-1 space-y-6">
            {/* User ID Card */}
            <UserIdCard />

            {/* Upload Section */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Upload Documents
              </h2>
              <UploadForm />
            </div>

            {/* Documents List */}
            <div>
              <DocumentList />
            </div>
          </div>

          {/* Right Column: Chat */}
          <div className="lg:col-span-2">
            <div className="h-96 lg:h-[600px]">
              <ChatInterface />
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-16">
        <div className="max-w-7xl mx-auto px-6 py-8 text-center text-sm text-gray-600">
          <p>
            Kamka Document Assistant • Powered by AI • All documents are
            securely processed
          </p>
        </div>
      </footer>
    </main>
  );
}
