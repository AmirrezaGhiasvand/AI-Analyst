"use client"

import * as React from "react"
import { Plus, Search } from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { NavMain } from "./nav-main"
import { useGetProjects } from "@/hooks/query/use-get-projects"
import Link from "next/link"
import { useParams } from "next/navigation"

// This is sample data.
const data = {
  navMain: [
    {
      title: "Search",
      url: "#",
      icon: Search,
    },
    {
      title: "New Project",
      url: "#",
      icon: Plus,
      badge: "10",
    },
  ],
}

export function ProjectsSidebar({
  ...props
}: React.ComponentProps<typeof Sidebar>) {
  const { data: projects } = useGetProjects()
  const params = useParams<{ projectId: string }>()
  const activeProjectId = params.projectId
  return (
    <Sidebar className="border-r-0 pt-2" collapsible="icon" {...props}>
      <SidebarHeader>
        {/* <TeamSwitcher teams={data.teams} /> */}
        <NavMain items={data.navMain} />
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Projects</SidebarGroupLabel>
          <SidebarGroupContent className="group-data-[collapsible=icon]:hidden">
            <SidebarMenu className="space-y-2">
              {projects?.map((project) => {
                return (
                  <SidebarMenuItem key={project.id}>
                    <SidebarMenuButton
                      className="transition-all duration-300"
                      render={
                        <Link href={`/projects/${project.id}`}>
                          {project.name}
                        </Link>
                      }
                      isActive={project.id === activeProjectId}
                    />
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
