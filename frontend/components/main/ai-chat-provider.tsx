import { UIDataTypes, UIMessage, UITools } from "ai"
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

type Props = {
  isBusy: boolean
  messages: UIMessage<unknown, UIDataTypes, UITools>[]
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
                  scrollAnchor={message.role === "user"}
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
                          {message.parts.map((part, i) =>
                            part.type === "text" ? (
                              <span key={i}>{part.text}</span>
                            ) : null
                          )}
                        </BubbleContent>
                      </Bubble>
                    </MessageContent>
                  </Message>
                </MessageScrollerItem>
              )
            })}
          </MessageScrollerContent>
        </MessageScrollerViewport>
        <MessageScrollerButton />
      </MessageScroller>
    </MessageScrollerProvider>
  )
}
