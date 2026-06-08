"use client";

import { useState } from "react";
import { useAppStore } from "@/lib/store";

export function UserIdCard() {
  const userId = useAppStore((state) => state.userId);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(userId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
      <p className="text-xs font-semibold text-blue-900 uppercase tracking-wide">
        Your User ID
      </p>
      <div className="flex items-center justify-between gap-3 mt-2">
        <code className="text-sm text-blue-700 font-mono break-all">
          {userId}
        </code>
        <button
          onClick={handleCopy}
          className="px-3 py-1 text-xs font-medium bg-blue-600 text-white rounded hover:bg-blue-700 transition whitespace-nowrap"
        >
          {copied ? "✓ Copied" : "Copy"}
        </button>
      </div>
      <p className="text-xs text-blue-600 mt-2">
        This ID ensures only you can access your documents.
      </p>
    </div>
  );
}
