"use client";

import React, { useState } from "react";

interface Citation {
  reference: string;
  filename: string;
  page: number | null;
  chunk_index: number | null;
  excerpt: string;
}

export function CitationCard({ citation }: { citation: Citation }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <p className="font-semibold text-amber-900">{citation.filename}</p>
          <p className="text-amber-800 text-xs mt-1">
            {citation.page
              ? `Page ${citation.page}`
              : `Chunk ${citation.chunk_index}`}{" "}
            • {citation.reference}
          </p>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-amber-700 hover:text-amber-900 font-semibold text-xs whitespace-nowrap"
        >
          {isExpanded ? "Hide" : "Show"}
        </button>
      </div>
      {isExpanded && (
        <div className="mt-2 pt-2 border-t border-amber-200">
          <p className="text-amber-900 italic line-clamp-3">
            {citation.excerpt}
          </p>
        </div>
      )}
    </div>
  );
}
