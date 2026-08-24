"use client"

import { type LucideIcon } from "lucide-react"

import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import NewProjectDialog from "../landing/new-project-dialog"

export function NavMain({
  items,
}: {
  items: {
    title: string
    url: string
    icon: LucideIcon
    isActive?: boolean
  }[]
}) {
  return (
    <SidebarMenu className="space-y-2">
      {items.map((item) => (
        <SidebarMenuItem key={item.title}>
          <SidebarMenuButton
            className="transition-all duration-300"
            render={
              <a href={item.url}>
                <item.icon />
                <span>{item.title}</span>
              </a>
            }
            isActive={item.isActive}
          />
        </SidebarMenuItem>
      ))}
      <SidebarMenuItem>
        <NewProjectDialog sidebar />
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
