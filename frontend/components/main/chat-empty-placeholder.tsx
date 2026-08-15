import { MessageCircleDashedIcon } from "lucide-react"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "../ui/empty"

export default function ChatEmptyPlaceholder() {
  return (
    <Empty className="h-full">
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <MessageCircleDashedIcon />
        </EmptyMedia>
        <EmptyTitle>Morning, shadcn!</EmptyTitle>
        <EmptyDescription>
          What are we working on today? Press send to start a new conversation
        </EmptyDescription>
      </EmptyHeader>
    </Empty>
  )
}
