import { Bubble, BubbleContent } from "../ui/bubble"
import { Message, MessageContent } from "../ui/message"
import {
  MessageScrollerContent,
  MessageScroller,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport,
  MessageScrollerButton,
} from "../ui/message-scroller"
import { cn } from "@/lib/utils"
import { ChatMessage } from "./ai-chat-sidebar"

type Props = {
  isBusy: boolean
  messages: ChatMessage[]
}

export default function AIChatProvider({ messages, isBusy }: Props) {
  return (
    <MessageScrollerProvider autoScroll defaultScrollPosition="end">
      <MessageScroller>
        <MessageScrollerViewport>
          <MessageScrollerContent aria-busy={isBusy} className="pb-10">
            {messages.map((message) => {
              const isUser = message.role === "user"

              return (
                <MessageScrollerItem
                  key={message.id}
                  messageId={message.id}
                  scrollAnchor={isUser}
                >
                  <Message align={isUser ? "end" : "start"}>
                    <MessageContent>
                      <Bubble variant={isUser ? "muted" : "ghost"}>
                        <BubbleContent
                          className={cn(
                            "text-[13px] leading-relaxed",
                            isUser ? "py-2" : "px-0 py-0"
                          )}
                        >
                          {message.content}
                        </BubbleContent>
                      </Bubble>
                    </MessageContent>
                  </Message>
                </MessageScrollerItem>
              )
            })}
            {isBusy && (
              <MessageScrollerItem messageId="loading" key={"loading"}>
                <Message align="start">
                  <MessageContent>
                    <Bubble variant="ghost">
                      <BubbleContent className="px-0 py-0">
                        <div className="flex items-center gap-1 py-2">
                          <span className="size-1.5 animate-bounce rounded-full bg-current [animation-delay:-0.3s]" />
                          <span className="size-1.5 animate-bounce rounded-full bg-current [animation-delay:-0.15s]" />
                          <span className="size-1.5 animate-bounce rounded-full bg-current" />
                        </div>
                      </BubbleContent>
                    </Bubble>
                  </MessageContent>
                </Message>
              </MessageScrollerItem>
            )}
          </MessageScrollerContent>
        </MessageScrollerViewport>
        <MessageScrollerButton />
      </MessageScroller>
    </MessageScrollerProvider>
  )
}
