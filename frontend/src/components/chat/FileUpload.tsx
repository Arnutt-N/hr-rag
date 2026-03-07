"use client";

import { useState, useRef } from "react";
import { motion } from "framer-motion";
import { Upload, X, FileText, Check } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

interface FileUploadProps {
  onUpload: (files: File[]) => void;
  className?: string;
}

export function FileUpload({ onUpload, className }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles((prev) => [...prev, ...droppedFiles]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles((prev) => [...prev, ...selectedFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setIsUploading(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    onUpload(files);
    setFiles([]);
    setIsUploading(false);
  };

  return (
    <div className={className}>
      <motion.div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          isDragging
            ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
            : "border-gray-300 dark:border-gray-600 hover:border-gray-400"
        }`}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt"
          onChange={handleFileSelect}
          className="hidden"
        />
        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-600 dark:text-gray-400 mb-2">
          ลากไฟล์มาวางที่นี่ หรือคลิกเพื่อเลือกไฟล์
        </p>
        <p className="text-sm text-gray-500">รองรับ PDF, DOC, DOCX, TXT</p>
      </motion.div>

      {files.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 space-y-2"
        >
          {files.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
            >
              <div className="flex items-center">
                <FileText className="w-5 h-5 text-primary-600 mr-3" />
                <div>
                  <p className="text-sm font-medium truncate max-w-xs">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <button
                onClick={() => removeFile(index)}
                className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>
          ))}

          <Button
            onClick={handleUpload}
            disabled={isUploading}
            className="w-full"
          >
            {isUploading ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                กำลังอัปโหลด...
              </>
            ) : (
              <>
                <Check className="w-4 h-4 mr-2" />
                อัปโหลด {files.length} ไฟล์
              </>
            )}
          </Button>
        </motion.div>
      )}
    </div>
  );
}
