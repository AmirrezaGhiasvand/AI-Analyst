"use client"

import { UIMessage, useChat } from "@ai-sdk/react"
import { createChat } from "@shadcn/helpers/ai-sdk"

const chat = createChat()
  .user(
    "I'm building a chat for our app and the scroll behavior is driving me nuts. Every time the AI streams a reply, the whole thread jumps around."
  )
  .assistant(({ writer }) => {
    writer.reasoning(
      "They are describing a streaming transcript that keeps taking control of the viewport. I should explain when auto-scroll follows and when it stops."
    )
    writer.text(
      "That's the classic streaming scroll problem. Wrap your message list in `MessageScroller` and turn on `autoScroll` — the viewport pins to the bottom as tokens arrive, so users always see the latest text land in place.\n\nThe important part: it only auto-scrolls while the reader is already at the bottom. The moment they scroll up to read something earlier, auto-scroll backs off and their position is preserved. You get smooth streaming without fighting the user's intent."
    )
  })
  .user(
    "Okay, but when someone sends a new message the view still feels jarring — like the whole conversation reloads from the top."
  )
  .assistant(
    "MessageScrollerItem fixes that with turn anchoring. Set `scrollAnchor` on the turn that should settle near the top instead of blindly snapping to the document bottom.\n\nIt also leaves a small peek of the previous exchange visible above the anchor, so context isn't lost. The reply starts in view without that disorienting jump you get from a plain overflow container."
  )
  .user(
    "And if they've scrolled up to re-read an older answer? I don't want to yank them back down."
  )
  .assistant(
    "You won't. Auto-scroll only runs when the viewport is already pinned to the bottom, so scrolling up is a deliberate opt-out — their place in the thread stays put even as new tokens keep arriving below.\n\nWhen there is content they haven't seen yet, `MessageScrollerButton` appears at the bottom of the viewport. One tap jumps them back to the newest message and re-engages auto-scroll. Same pattern as Slack or iMessage: quiet when you're caught up, helpful when you're not."
  )
  .user("Last one — does this work with assistive tech?")
  .assistant(
    '`MessageScrollerContent` sets `role="log"` and `aria-relevant="additions"` by default, so screen readers announce new messages as they stream in.\n\nThe scroll button is a real `<button>` with an sr-only label, and it\'s removed from the tab order when you\'re already at the bottom — no ghost focus stops.'
  )

const initialMessages = chat.get(0)
const transport = chat.transport()

function getMessageText(message: UIMessage) {
  return message.parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("")
}

export function useAIChat() {
  const { messages, sendMessage, status } = useChat({
    messages: initialMessages,
    transport,
  })

  const nextMessage = chat.next(messages)
  const isBusy = status === "submitted" || status === "streaming"

  return {
    messages,
    nextMessage,
    isBusy,
    sendMessage,
    getMessageText,
  }
}
