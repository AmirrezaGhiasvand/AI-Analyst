import { useCallback, useState } from "react"

const MIN_WIDTH = 320
const MAX_WIDTH = 560

export default function useHandleResizeSidebar() {
  const [width, setWidth] = useState(MIN_WIDTH)
  const [isResizing, setIsResizing] = useState(false)

  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault()
      setIsResizing(true)

      const startX = e.clientX
      const startWidth = width

      const handlePointerMove = (moveEvent: PointerEvent) => {
        // sidebar is on the right (border-l), so dragging the
        // left edge left should grow it, right should shrink it
        const delta = startX - moveEvent.clientX
        const next = Math.min(
          MAX_WIDTH,
          Math.max(MIN_WIDTH, startWidth + delta)
        )
        setWidth(next)
      }

      const handlePointerUp = () => {
        document.removeEventListener("pointermove", handlePointerMove)
        document.removeEventListener("pointerup", handlePointerUp)
        setIsResizing(false)
      }

      document.addEventListener("pointermove", handlePointerMove)
      document.addEventListener("pointerup", handlePointerUp)
    },
    [width]
  )

  return {
    handlePointerDown,
    isResizing,
    width,
  }
}
