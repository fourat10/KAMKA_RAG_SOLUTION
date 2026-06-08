"use client";

import { parseMarkdownBold } from "@/lib/utils";

export function MarkdownText({ text }: { text: string }) {
  const parts = parseMarkdownBold(text);

  return (
    <>
      {parts.map((part, index) => {
        if (typeof part === "string") {
          return <span key={index}>{part}</span>;
        }
        if (part.type === "bold") {
          return (
            <strong key={index} className="font-semibold">
              {part.content}
            </strong>
          );
        }
        return null;
      })}
    </>
  );
}
