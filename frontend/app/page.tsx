import ChatInput from "@/components/landing/chat-input"
import SpotlightBackground from "@/components/landing/spotlight-background"

export default function Page() {
  return (
    <>
      <div className="flex h-[80vh] w-full items-center justify-center">
        <ChatInput />
      </div>
      <SpotlightBackground />
    </>
  )
}
