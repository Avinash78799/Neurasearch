import React, { useState, useRef } from "react";
import { Upload, Loader2, CheckCircle2, ShieldAlert, Sparkles } from "lucide-react";
import toast from "react-hot-toast";

export default function DocumentUpload({ onUploadComplete, proMode, documentsCount }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const fileInputRef = useRef(null);

  const isLimitReached = !proMode && documentsCount >= 3;

  const handleFile = async (file) => {
    if (!file) return;

    if (isLimitReached) {
      toast.error("Free Tier document limit reached (3 files max). Upgrade to Pro!");
      return;
    }

    setIsUploading(true);
    setUploadSuccess(false);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/v1/ingest", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        setUploadSuccess(true);
        onUploadComplete?.();
        toast.success("Document uploaded and ingested successfully!");
        setTimeout(() => setUploadSuccess(false), 2500);
      } else {
        const err = await res.json();
        toast.error(err.detail || "Upload failed.");
      }
    } catch {
      toast.error("Network error during upload.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (isLimitReached) return;
    const file = e.dataTransfer.files?.[0];
    handleFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (isLimitReached) return;
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleClick = () => {
    if (isLimitReached) {
      toast.error("Free Tier document limit reached. Please upgrade to Pro!");
      return;
    }
    fileInputRef.current?.click();
  };

  const handleInputChange = (e) => {
    const file = e.target.files?.[0];
    handleFile(file);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onKeyDown={(e) => e.key === "Enter" && handleClick()}
      className={`
        relative flex flex-col items-center justify-center gap-2
        rounded-xl border-2 border-dashed p-5 cursor-pointer
        transition-all duration-300
        ${
          isLimitReached
            ? "border-neon-violet/20 bg-neon-violet/5 cursor-not-allowed hover:bg-neon-violet/10"
            : isDragging
            ? "border-neon-cyan bg-neon-cyan/[.06] neon-glow-cyan"
            : uploadSuccess
            ? "border-neon-emerald/50 bg-neon-emerald/[.04]"
            : "border-dark-600 hover:border-gray-500 hover:bg-dark-700/40"
        }
      `}
    >
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt"
        disabled={isLimitReached}
        onChange={handleInputChange}
        className="hidden"
      />

      {/* Icon */}
      {isLimitReached ? (
        <ShieldAlert className="w-6 h-6 text-neon-violet animate-pulse" />
      ) : isUploading ? (
        <Loader2 className="w-6 h-6 text-neon-cyan animate-spin" />
      ) : uploadSuccess ? (
        <CheckCircle2 className="w-6 h-6 text-neon-emerald" />
      ) : (
        <Upload
          className={`w-6 h-6 transition-colors duration-300 ${
            isDragging ? "text-neon-cyan" : "text-gray-500"
          }`}
        />
      )}

      {/* Text */}
      <div className="text-center">
        <p
          className={`text-xs font-semibold transition-colors duration-300 ${
            isLimitReached
              ? "text-neon-violet"
              : isUploading
              ? "text-neon-cyan"
              : uploadSuccess
              ? "text-neon-emerald"
              : isDragging
              ? "text-neon-cyan"
              : "text-gray-400"
          }`}
        >
          {isLimitReached
            ? "Document Cap Reached"
            : isUploading
            ? "Ingesting document..."
            : uploadSuccess
            ? "Ingestion Complete"
            : "Drop PDF/TXT here or click"}
        </p>
        
        {isLimitReached ? (
          <p className="text-[10px] text-gray-500 mt-1 leading-normal">
            Max 3 docs on Free Tier. Upgrade to Pro for unlimited.
          </p>
        ) : (
          !isUploading && !uploadSuccess && (
            <p className="text-[10px] text-gray-600 mt-1">
              PDF or TXT up to 10MB
            </p>
          )
        )}
      </div>
    </div>
  );
}
