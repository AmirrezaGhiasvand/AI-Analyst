"use client"

import { Sidebar, SidebarContent, SidebarFooter } from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"
import { ArrowUp, GripVertical, PlusIcon } from "lucide-react"
import { ComponentProps, CSSProperties } from "react"
import useHandleResizeSidebar from "@/hooks/use-handle-resize-sidebar"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupInput,
  InputGroupTextarea,
} from "../ui/input-group"
import { useAIChat } from "@/hooks/use-ai-chat"
import ChatEmptyPlaceholder from "./chat-empty-placeholder"
import AIChatProvider from "./ai-chat-provider"

export function AIChatSidebar({
  className,
  ...props
}: ComponentProps<typeof Sidebar>) {
  const { isResizing, handlePointerDown, width } = useHandleResizeSidebar()
  const { getMessageText, isBusy, messages, nextMessage, sendMessage } =
    useAIChat()

  return (
    <Sidebar
      collapsible="none"
      className={cn(
        "sticky top-0 hidden h-svh border-l lg:flex",
        "relative", // needed so the handle can be absolutely positioned
        className
      )}
      style={{ "--sidebar-width": `${width}px` } as CSSProperties}
      {...props}
    >
      {/* resize handle */}
      <div
        role="separator"
        aria-orientation="vertical"
        onPointerDown={handlePointerDown}
        className={cn(
          "group/handle absolute inset-y-0 inset-s-0 z-20 w-4 -translate-x-1/2",
          "cursor-col-resize touch-none select-none",
          // thin line, only visible on hover/drag
          "after:absolute after:inset-y-0 after:inset-s-1/2 after:w-px after:-translate-x-1/2",
          "after:bg-transparent hover:after:bg-border",
          isResizing && "after:bg-primary"
        )}
      >
        {/* grip pill, centered vertically */}
        <div
          className={cn(
            "absolute inset-s-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2",
            "flex h-10 w-4 items-center justify-center rounded-full border bg-border",
            "z-50 opacity-0 transition-opacity duration-150",
            "group-hover/handle:opacity-100",
            isResizing && "border-primary bg-primary opacity-100"
          )}
        >
          <GripVertical
            className={cn(
              "size-3 text-muted-foreground",
              isResizing && "text-primary-foreground"
            )}
          />
        </div>
      </div>

      <SidebarContent className="h-full py-2 pl-3">
        {messages.length === 0 ? (
          <ChatEmptyPlaceholder />
        ) : (
          <AIChatProvider messages={messages} isBusy={isBusy} />
        )}
      </SidebarContent>
      <SidebarFooter className="relative px-2 py-1">
        <div className="pointer-events-none absolute inset-x-0 -top-12 h-12 bg-linear-to-t from-sidebar to-transparent" />

        <div className="relative rounded-xl border border-border bg-card">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              if (!nextMessage || isBusy) {
                return
              }
              void sendMessage(nextMessage)
            }}
            className="w-full"
          >
            <InputGroup>
              {/* <InputGroupTextarea
                // value={nextMessage ? getMessageText(nextMessage) : ""}
                disabled={!nextMessage || isBusy}
                // readOnly
                rows={1}
              /> */}
              <InputGroupInput />
              <InputGroupAddon align="inline-start">
                <InputGroupButton variant="ghost" size="icon-xs">
                  <PlusIcon className="size-4" />
                </InputGroupButton>
              </InputGroupAddon>
              <InputGroupAddon align="inline-end">
                <InputGroupButton
                  variant="default"
                  size="icon-xs"
                  className="ml-auto"
                  type="submit"
                >
                  <ArrowUp className="size-4" />
                </InputGroupButton>
              </InputGroupAddon>
            </InputGroup>
          </form>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
