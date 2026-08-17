import { SidebarProvider } from "@/components/ui/sidebar"

export default function ProjectsLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return <SidebarProvider>{children}</SidebarProvider>
}
