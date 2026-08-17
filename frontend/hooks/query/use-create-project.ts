// api/chat.ts

import { client } from "@/api/axios-client"
import { endpoints } from "@/api/endpoints"
import { useMutation } from "@tanstack/react-query"

type CreateProjectRequest = {
  project_name: string
  file: File
}

type CreateProjectResponse = {
  project: {
    id: string
    name: string
  }
}

async function createProject(
  request: CreateProjectRequest
): Promise<CreateProjectResponse> {
  const formData = new FormData()
  formData.append("project_name", request.project_name)
  formData.append("file", request.file)
  const { data } = await client.post<CreateProjectResponse>(
    `${endpoints.datasets}`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  )

  return data
}

export function useCreateProject() {
  return useMutation({
    mutationFn: (request: CreateProjectRequest) => createProject(request),
  })
}
