"use client";

import React, { useState, useRef, useEffect } from "react";
import { apiService, type Citation } from "@/lib/api";
import { useAppStore, type ChatMessage } from "@/lib/store";
import { CitationCard } from "./CitationCard";
import { MarkdownText } from "./MarkdownText";
import { ResumeCard } from "./ResumeCard";

// Helper function to detect if content is a resume
const isResumeContent = (content: string): boolean => {
  const resumeKeywords = [
    "Education",
    "Technical Skills",
    "Work Experience",
    "Projects",
    "Contact information",
  ];
  return resumeKeywords.some((keyword) =>
    content.toLowerCase().includes(keyword.toLowerCase()),
  );
};

export function ChatInterface() {
  const userId = useAppStore((state) => state.userId);
  const sessionId = useAppStore((state) => state.sessionId);
  const setSessionId = useAppStore((state) => state.setSessionId);
  const selectedDocIds = useAppStore((state) => state.selectedDocIds);
  const messages = useAppStore((state) => state.messages);
  const addMessage = useAppStore((state) => state.addMessage);
  const isLoading = useAppStore((state) => state.isLoading);
  const setIsLoading = useAppStore((state) => state.setIsLoading);
  const error = useAppStore((state) => state.error);
  const setError = useAppStore((state) => state.setError);

  const [input, setInput] = useState("");
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingCitations, setStreamingCitations] = useState<Citation[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Generate session ID on component mount if not already set
  useEffect(() => {
    if (!sessionId) {
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
      setSessionId(newSessionId);
    }
  }, [sessionId, setSessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || selectedDocIds.length === 0 || isLoading) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };

    addMessage(userMessage);
    setInput("");
    setIsLoading(true);
    setError(null);
    setStreamingContent("");
    setStreamingCitations([]);

    let finalContent = "";
    let finalCitations: Citation[] = [];

    try {
      await apiService.chatStream(
        input,
        selectedDocIds,
        userId,
        sessionId,
        (token) => {
          // Handle incoming token
          finalContent += token;
          setStreamingContent((prev) => prev + token);
        },
        (citations) => {
          // Handle citations
          finalCitations = citations;
          setStreamingCitations(citations);
        },
      );

      // Add final message to store
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: "assistant",
        content: finalContent,
        citations: finalCitations,
        timestamp: new Date().toISOString(),
      };
      addMessage(assistantMessage);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to get response";
      setError(message);
    } finally {
      setIsLoading(false);
      setStreamingContent("");
      setStreamingCitations([]);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Chat</h2>
        {selectedDocIds.length === 0 ? (
          <p className="text-sm text-red-600 mt-1">Select documents to chat</p>
        ) : (
          <p className="text-sm text-gray-600 mt-1">
            Chatting with {selectedDocIds.length} document
            {selectedDocIds.length !== 1 ? "s" : ""}
          </p>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && !isLoading ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>Start a conversation by typing a message</p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {isResumeContent(msg.content) && msg.role === "assistant" ? (
                  <div className="w-full">
                    <ResumeCard content={msg.content} />
                  </div>
                ) : (
                  <div
                    className={`max-w-lg rounded-lg p-4 ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-900"
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">
                      <MarkdownText text={msg.content} />
                    </p>

                    {msg.role === "assistant" &&
                      msg.citations &&
                      msg.citations.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-300 space-y-2">
                          <p className="text-xs font-semibold text-gray-600">
                            Sources:
                          </p>
                          {msg.citations.map((citation, i) => (
                            <CitationCard key={i} citation={citation} />
                          ))}
                        </div>
                      )}
                  </div>
                )}
              </div>
            ))}

            {isLoading && streamingContent && (
              <div className="flex gap-3 justify-start w-full">
                {isResumeContent(streamingContent) ? (
                  <div className="w-full opacity-75">
                    <ResumeCard content={streamingContent} />
                    <div className="mt-2 text-center text-xs text-gray-500 italic">
                      streaming...
                    </div>
                  </div>
                ) : (
                  <div className="max-w-lg rounded-lg p-4 bg-gray-100 text-gray-900">
                    <p className="text-sm whitespace-pre-wrap">
                      <MarkdownText text={streamingContent} />
                    </p>
                    <div className="mt-2 text-xs text-gray-500 italic">
                      streaming...
                    </div>
                    {streamingCitations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-300 space-y-2">
                        <p className="text-xs font-semibold text-gray-600">
                          Sources:
                        </p>
                        {streamingCitations.map((citation, i) => (
                          <CitationCard key={i} citation={citation} />
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {isLoading && !streamingContent && (
              <div className="flex gap-3 justify-start">
                <div className="bg-gray-100 rounded-lg p-4">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></div>
                    <div
                      className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                    <div
                      className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
                      style={{ animationDelay: "0.4s" }}
                    ></div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-6">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              selectedDocIds.length === 0
                ? "Select documents first..."
                : "Ask a question..."
            }
            disabled={selectedDocIds.length === 0 || isLoading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={selectedDocIds.length === 0 || isLoading || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
