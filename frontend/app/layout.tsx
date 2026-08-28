"use client"
import { Plus_Jakarta_Sans } from "next/font/google"

import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { cn } from "@/lib/utils"
import { Toaster } from "@/components/ui/toast"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ChatProvider } from "@/context/chat-store"

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
})

const fontMono = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-mono",
})

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnReconnect: "always",
      refetchOnWindowFocus: false,
    },
  },
})

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn(
        "antialiased",
        fontMono.variable,
        "font-sans",
        plusJakartaSans.variable
      )}
    >
      <body>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <ChatProvider>{children}</ChatProvider>
          </ThemeProvider>
          <Toaster />
        </QueryClientProvider>
      </body>
    </html>
  )
}
