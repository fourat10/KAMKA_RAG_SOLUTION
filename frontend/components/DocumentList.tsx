"use client";

import { useAppStore, type Document } from "@/lib/store";
import { formatDate } from "@/lib/utils";

export function DocumentList() {
  const documents = useAppStore((state) => state.documents);
  const selectedDocIds = useAppStore((state) => state.selectedDocIds);
  const toggleDocumentSelection = useAppStore(
    (state) => state.toggleDocumentSelection,
  );

  if (documents.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No documents uploaded yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-gray-900 text-sm">
        Your Documents ({documents.length})
      </h3>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {documents.map((doc) => (
          <DocumentItem
            key={doc.document_id}
            doc={doc}
            isSelected={selectedDocIds.includes(doc.document_id)}
            onToggle={() => toggleDocumentSelection(doc.document_id)}
          />
        ))}
      </div>
    </div>
  );
}

function DocumentItem({
  doc,
  isSelected,
  onToggle,
}: {
  doc: Document;
  isSelected: boolean;
  onToggle: () => void;
}) {
  return (
    <div
      onClick={onToggle}
      className={`p-3 rounded-lg border-2 cursor-pointer transition ${
        isSelected
          ? "border-blue-500 bg-blue-50"
          : "border-gray-200 bg-white hover:border-gray-300"
      }`}
    >
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggle}
          className="mt-1 w-4 h-4 cursor-pointer"
        />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 truncate">{doc.filename}</p>
          <p className="text-xs text-gray-500 mt-1">
            {doc.chunk_count} chunks • {formatDate(doc.uploaded_at)}
          </p>
        </div>
      </div>
    </div>
  );
}
