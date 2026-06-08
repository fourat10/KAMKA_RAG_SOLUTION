"use client";

import { useState } from "react";
import { apiService } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { formatFileSize } from "@/lib/utils";

export function UploadForm() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const userId = useAppStore((state) => state.userId);
  const addDocument = useAppStore((state) => state.addDocument);
  const setError = useAppStore((state) => state.setError);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFile = async (file: File) => {
    if (!userId) {
      setError("User ID not initialized");
      return;
    }

    const validExtensions = [".pdf", ".txt"];
    const fileExtension = "." + file.name.split(".").pop()?.toLowerCase();

    if (!validExtensions.includes(fileExtension)) {
      setError("Only PDF and TXT files are allowed");
      return;
    }

    const maxSizeMB = 20;
    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`File must be smaller than ${maxSizeMB}MB`);
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const result = await apiService.uploadDocument(file, userId);
      addDocument({
        document_id: result.document_id,
        filename: result.filename,
        chunk_count: result.chunk_count,
        cloudinary_url: result.cloudinary_url,
        uploaded_at: result.uploaded_at,
      });
    } catch (err) {
      let message = "Failed to upload file";
      if (err instanceof Error) {
        message = err.message;
      }
      // Try to get the actual error detail from axios response
      if (err && typeof err === "object" && "response" in err) {
        const response = (err as any).response;
        if (response?.data?.detail) {
          message = response.data.detail;
        }
      }
      setError(message);
      console.error("Upload error:", err);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
        isDragging
          ? "border-blue-500 bg-blue-50"
          : "border-gray-300 bg-gray-50 hover:border-gray-400"
      } ${isUploading ? "opacity-60 pointer-events-none" : ""}`}
    >
      <div className="flex flex-col items-center gap-4">
        <div className="text-4xl">📄</div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Drag and drop your file here
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            or click to browse (PDF or TXT, max 20MB)
          </p>
        </div>

        <label className="cursor-pointer">
          <input
            type="file"
            onChange={handleFileInput}
            accept=".pdf,.txt"
            disabled={isUploading}
            className="hidden"
          />
          <span className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium">
            {isUploading ? "Uploading..." : "Select File"}
          </span>
        </label>
      </div>
    </div>
  );
}
