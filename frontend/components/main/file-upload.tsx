"use client"

import React, { useRef, useState } from "react"
import { cn } from "@/lib/utils"
import { useDropzone } from "react-dropzone"
import { motion } from "motion/react"
import { Upload, X } from "lucide-react"

const mainVariant = {
  initial: { x: 0, y: 0 },
  animate: { x: 20, y: -20, opacity: 0.9 },
}

const secondaryVariant = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
}

// Accepted dataset MIME types + extensions
const ACCEPTED_TYPES: Record<string, string[]> = {
  "text/csv": [".csv"],
  "text/tab-separated-values": [".tsv"],
  "application/json": [".json"],
  "application/vnd.ms-excel": [".xls"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
    ".xlsx",
  ],
  "application/x-parquet": [".parquet"],
}

const ACCEPTED_EXTENSIONS = [
  ".csv",
  ".tsv",
  ".json",
  ".xls",
  ".xlsx",
  ".parquet",
]

const isDatasetFile = (file: File) => {
  const ext = "." + (file.name.split(".").pop()?.toLowerCase() ?? "")
  return ACCEPTED_EXTENSIONS.includes(ext)
}

interface FileUploadProps {
  onChange?: (files: File[]) => void
}

export const FileUpload: React.FC<FileUploadProps> = ({ onChange }) => {
  const [files, setFiles] = useState<File[]>([])
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (newFiles: File[]) => {
    // Only allow one file at a time
    if (files.length > 0) {
      return
    }

    const valid = newFiles.filter(isDatasetFile)
    const invalid = newFiles.filter((f) => !isDatasetFile(f))

    if (invalid.length > 0) {
      setError(
        `Unsupported file type: ${invalid[0].name}. Accepted: ${ACCEPTED_EXTENSIONS.join(", ")}`
      )
    } else {
      setError(null)
    }

    if (valid.length === 0) return

    setFiles((prev) => [...prev, ...valid])
    onChange?.(valid)
  }

  const handleRemoveFile = (e: React.MouseEvent) => {
    e.stopPropagation()
    setFiles([])
    setError(null)
    onChange?.([])
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const { getRootProps, isDragActive } = useDropzone({
    multiple: false,
    noClick: true,
    accept: ACCEPTED_TYPES,
    onDrop: handleFileChange,
    onDropRejected: (rejections) => {
      const name = rejections[0]?.file.name ?? "file"
      setError(
        `Unsupported file type: ${name}. Accepted: ${ACCEPTED_EXTENSIONS.join(", ")}`
      )
    },
  })

  const formatFileSize = (size: number) => (size / (1024 * 1024)).toFixed(2)

  const formatDate = (timestamp: number) =>
    new Date(timestamp).toLocaleDateString()

  return (
    <div className="w-full" {...getRootProps()}>
      <motion.div
        onClick={files.length === 0 ? handleClick : undefined}
        whileHover="animate"
        className={cn(
          "group/file relative block w-full overflow-hidden rounded-lg p-6",
          files.length <= 0 && "cursor-pointer"
        )}
      >
        <input
          ref={fileInputRef}
          id="file-upload-handle"
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(",")}
          onChange={(e) => handleFileChange(Array.from(e.target.files || []))}
          className="hidden"
        />
        <div className="flex flex-col items-center justify-center">
          <p className="relative z-20 mt-2 text-base text-muted-foreground">
            Drag or drop your files here or click to upload
          </p>
          <p className="relative z-20 mt-1 text-xs text-muted-foreground/70">
            {ACCEPTED_EXTENSIONS.join(", ")}
          </p>
          <div className="relative mx-auto mt-5 w-full max-w-xl">
            {files.length > 0 ? (
              files.map((file, idx) => (
                <FileItem
                  key={file.name + idx}
                  file={file}
                  onRemove={handleRemoveFile}
                  formatFileSize={formatFileSize}
                  formatDate={formatDate}
                  isFirst={idx === 0}
                />
              ))
            ) : (
              <EmptyState isDragActive={isDragActive} />
            )}
          </div>
          {error && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="relative z-20 mt-3 text-xs text-destructive"
            >
              {error}
            </motion.p>
          )}
        </div>
      </motion.div>
    </div>
  )
}

// File Item Component
interface FileItemProps {
  file: File
  formatFileSize: (size: number) => string
  formatDate: (timestamp: number) => string
  onRemove: (e: React.MouseEvent) => void
  isFirst: boolean
}
const FileItem: React.FC<FileItemProps> = ({
  file,
  formatFileSize,
  formatDate,
  onRemove,
  isFirst,
}) => (
  <motion.div
    layoutId={isFirst ? "file-upload" : `file-upload-${file.name}`}
    className={cn(
      "relative z-40 mx-auto mt-4 flex w-full flex-col items-start justify-start overflow-hidden rounded-md border bg-card p-4 shadow-sm md:h-24"
    )}
  >
    <div className="flex w-full items-center justify-between gap-4">
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        layout
        className="max-w-50 truncate text-sm font-medium text-foreground"
      >
        {file.name}
      </motion.p>
      <div className="flex gap-1">
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          layout
          className="w-fit shrink-0 rounded-lg bg-muted px-2 py-1 text-xs font-medium text-muted-foreground shadow-sm"
        >
          {formatFileSize(file.size)} MB
        </motion.p>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          layout
          className="w-fit shrink-0 cursor-pointer rounded-lg bg-muted px-2 py-1 text-xs font-medium text-muted-foreground shadow-sm"
          onClick={onRemove}
        >
          <X size={15} />
        </motion.p>
      </div>
    </div>
    <div className="mt-2 flex w-full flex-col items-start justify-between text-sm text-muted-foreground md:flex-row md:items-center">
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        layout
        className="rounded-md bg-muted px-3 py-1 text-xs"
      >
        {file.type}
      </motion.p>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        layout
        className="text-sm"
      >
        modified {formatDate(file.lastModified)}
      </motion.p>
    </div>
  </motion.div>
)

// Empty State Component
interface EmptyStateProps {
  isDragActive: boolean
}
const EmptyState: React.FC<EmptyStateProps> = ({ isDragActive }) => (
  <>
    <motion.div
      layoutId="file-upload"
      variants={mainVariant}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 20,
      }}
      className={cn(
        "relative z-40 mx-auto mt-4 flex h-28 w-full max-w-32 items-center justify-center rounded-md border bg-card shadow-sm transition-shadow group-hover/file:shadow-xl"
      )}
    >
      {isDragActive ? (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          layout
          className="flex flex-col items-center text-muted-foreground"
        >
          Drop it
          <Upload size={24} className="mt-2 h-6 w-6 shrink-0 text-primary" />
        </motion.p>
      ) : (
        <Upload size={24} className="h-6 w-6 shrink-0 text-muted-foreground" />
      )}
    </motion.div>
    <motion.div
      variants={secondaryVariant}
      className="absolute inset-0 z-30 mx-auto mt-4 flex h-28 w-full max-w-32 items-center justify-center rounded-md border border-dashed border-primary/50 bg-primary/5 opacity-0"
    />
  </>
)

const FileUploadMotion = () => {
  const [file, setFile] = useState<File[]>([])
  const handleFileUpload = (files: File[]) => {
    setFile(files)
  }
  return (
    <div className="mx-auto flex min-h-96 w-full max-w-4xl items-center justify-center rounded-xl border border-dashed border-muted bg-background p-10">
      <FileUpload onChange={handleFileUpload} />
    </div>
  )
}

export default FileUploadMotion
