"use client"

import { motion, useMotionTemplate, useMotionValue } from "motion/react"
import { type ReactNode, useEffect } from "react"

import { cn } from "@/lib/utils"

interface SpotlightRevealProps {
  children: ReactNode
  className?: string
  size?: number
  opacity?: number
}

export function SpotlightReveal({
  children,
  className,
  size = 300,
  opacity = 1,
}: SpotlightRevealProps) {
  const x = useMotionValue(-size * 2)
  const y = useMotionValue(-size * 2)
  const visible = useMotionValue(0)

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      x.set(event.clientX)
      y.set(event.clientY)
      visible.set(1)
    }

    const handleMouseLeave = () => {
      visible.set(0)
    }

    const handleMouseEnter = (event: MouseEvent) => {
      x.set(event.clientX)
      y.set(event.clientY)
      visible.set(1)
    }

    window.addEventListener("mousemove", handleMouseMove)
    document.documentElement.addEventListener("mouseleave", handleMouseLeave)
    document.documentElement.addEventListener("mouseenter", handleMouseEnter)

    return () => {
      window.removeEventListener("mousemove", handleMouseMove)
      document.documentElement.removeEventListener(
        "mouseleave",
        handleMouseLeave
      )
      document.documentElement.removeEventListener(
        "mouseenter",
        handleMouseEnter
      )
    }
  }, [x, y, visible])

  const maskImage = useMotionTemplate`
    radial-gradient(
      circle ${size}px at ${x}px ${y}px,
      black 0%,
      transparent 100%
    )
  `

  return (
    <motion.div
      className={cn("pointer-events-none fixed inset-0 z-0", className)}
      style={{
        maskImage,
        WebkitMaskImage: maskImage,
        opacity: useMotionTemplate`${visible}`,
      }}
    >
      {children}
    </motion.div>
  )
}
