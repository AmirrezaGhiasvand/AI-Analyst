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

export async function getProjects(): Promise<Project[]> {
  const { data } = await client.get<Project[]>(endpoints.projects)
  return data
}

export function useGetProjects() {
  return useQuery({
    queryKey: [queryKeys.projects],
    queryFn: getProjects,
  })
}
