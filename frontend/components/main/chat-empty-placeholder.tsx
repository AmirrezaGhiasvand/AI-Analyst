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
        <EmptyTitle>Morning, analyst!</EmptyTitle>
        <EmptyDescription>
          Lets have a data driven conversation.
        </EmptyDescription>
      </EmptyHeader>
    </Empty>
  )
}
