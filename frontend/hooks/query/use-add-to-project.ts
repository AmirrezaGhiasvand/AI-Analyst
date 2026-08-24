// api/chat.ts

import { client } from "@/api/axios-client"
import { endpoints } from "@/api/endpoints"
import { useMutation } from "@tanstack/react-query"

type AddToProjectRequest = {
  project_id: string
  file: File
}

type AddToProjectResponse = {
  project: {
    id: string
    name: string
  }
}

async function addToProject(
  request: AddToProjectRequest
): Promise<AddToProjectResponse> {
  const formData = new FormData()
  formData.append("project_id", request.project_id)
  formData.append("file", request.file)
  const { data } = await client.post<AddToProjectResponse>(
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

export function useAddToProject() {
  return useMutation({
    mutationFn: (request: AddToProjectRequest) => addToProject(request),
  })
}
