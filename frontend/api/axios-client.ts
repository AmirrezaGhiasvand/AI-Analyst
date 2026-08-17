import { toast } from "@/components/ui/toast"
import axios, { AxiosError } from "axios"

export const client = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 30_000,
  headers: {
    "Content-Type": "application/json",
  },
})

client.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.status === 404) {
      window.location.replace("/projects")
      return
    }
    toast.add({
      id: `error-${error.code}`,
      type: "error",
      description: error.message,
    })

    return Promise.reject(error)
  }
)
