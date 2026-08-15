import { endpoints } from "./../../api/endpoints"
import { client } from "@/api/axios-client"
import { queryKeys } from "@/api/queryKeys"
import { useQuery } from "@tanstack/react-query"

export type Project = {
  id: string
  name: string
  createdAt: string
  updatedAt: string
}

export async function getProject(projectId: string): Promise<Project> {
  const { data } = await client.get<Project>(
    `${endpoints.projects}/${projectId}`
  )
  return data
}

export function useGetProject(projectId: string) {
  return useQuery({
    queryKey: [queryKeys.projects, projectId],
    queryFn: () => getProject(projectId),
    enabled: !!projectId,
  })
}
