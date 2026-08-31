import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function deriveProjectName(message: string, wordCount = 3) {
  const words = message.trim().split(/\s+/).slice(0, wordCount)
  let name = words.join(" ")
  if (words.length < message.trim().split(/\s+/).length) {
    name += "…"
  }
  return name
}
