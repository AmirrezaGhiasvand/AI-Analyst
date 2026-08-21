import { PlusIcon } from "lucide-react"
import { Button } from "../ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog"
import { Label } from "../ui/label"
import { Input } from "../ui/input"
import { FileUpload } from "../main/file-upload"
import { useCreateProject } from "@/hooks/query/use-create-project"
import { useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select"
import { useGetProjects } from "@/hooks/query/use-get-projects"
import { useAddToProject } from "@/hooks/query/use-add-to-project"
import { SidebarMenuButton } from "../ui/sidebar"

export default function NewProjectDialog({ sidebar }: { sidebar?: boolean }) {
  const router = useRouter()
  const { data: projects, isLoading: isProjectsLoading } = useGetProjects()

  const { mutateAsync: createProject, isPending: isCreatingProject } =
    useCreateProject()
  const { mutateAsync: addToProject, isPending: isAddingToProject } =
    useAddToProject()

  const [projectDialogOpen, setProjectDialogOpen] = useState(false)
  const [projectName, setProjectName] = useState("")
  const [datasetFile, setDatasetFile] = useState<File | null>(null)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>()

  const projectItems = useMemo(
    () =>
      (projects ?? []).map((project) => ({
        label: project.name,
        value: project.id,
      })),
    [projects]
  )

  const isSelectDisabled = projectName.trim().length > 0
  const isNameInputDisabled = !!selectedProjectId
  const isExistingProjectMode = !!selectedProjectId
  const isSubmitting = isCreatingProject || isAddingToProject

  const handleFileChange = (files: File[]) => {
    setDatasetFile(files[0] ?? null)
  }

  const handleCreateProject = async () => {
    if (!projectName.trim() || !datasetFile) return
    try {
      const { project: newProject } = await createProject({
        project_name: projectName,
        file: datasetFile,
      })
      router.replace(`/projects/${newProject.id}`)
    } catch {}

    setProjectDialogOpen(false)
    setProjectName("")
    setDatasetFile(null)
  }

  const handleAddToProject = async () => {
    if (!selectedProjectId || !datasetFile) return
    try {
      const { project: existingProject } = await addToProject({
        project_id: selectedProjectId,
        file: datasetFile,
      })
      router.replace(`/projects/${existingProject.id}`)
    } catch {}

    setProjectDialogOpen(false)
    setProjectName("")
    setDatasetFile(null)
  }

  const handleSubmit = () => {
    if (isExistingProjectMode) {
      handleAddToProject()
    } else {
      handleCreateProject()
    }
  }

  const isSubmitDisabled = isExistingProjectMode
    ? !selectedProjectId || !datasetFile || isSubmitting
    : !projectName.trim() || !datasetFile || isSubmitting

  return (
    <Dialog open={projectDialogOpen} onOpenChange={setProjectDialogOpen}>
      <DialogTrigger
        render={
          sidebar ? (
            <SidebarMenuButton
              className="cursor-pointer transition-all duration-300"
              render={
                <button>
                  <PlusIcon />
                  Project
                </button>
              }
            />
          ) : (
            <Button
              type="button"
              size="sm"
              variant="secondary"
              className="flex cursor-pointer items-center justify-between gap-1 rounded-lg border border-dashed border-border px-2 py-1 text-sm transition-colors"
            >
              <PlusIcon className="h-4 w-4" />
              Project
            </Button>
          )
        }
      />
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create project (Or select an existing one)</DialogTitle>
          <DialogDescription>
            Give your project a name and upload a dataset to get started.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <div className="grid gap-2">
            <Label htmlFor="existing-project">Existing projects</Label>

            <Select
              items={projectItems}
              id="existing-project"
              disabled={isSelectDisabled}
              value={selectedProjectId}
              onValueChange={(value) => setSelectedProjectId(value)}
            >
              <SelectTrigger>
                <SelectValue
                  placeholder={
                    isProjectsLoading
                      ? "Loading projects..."
                      : projectItems.length === 0
                        ? "No projects yet"
                        : "Select a project"
                  }
                />
              </SelectTrigger>
              <SelectContent alignItemWithTrigger={false}>
                <SelectGroup>
                  {projectItems.map((project) => (
                    <SelectItem key={project.value} value={project.value}>
                      {project.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="project-name">Project name</Label>
            <Input
              id="project-name"
              placeholder="Persian Food Analysis"
              value={projectName}
              disabled={isNameInputDisabled}
              onChange={(e) => setProjectName(e.target.value)}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="dataset-file">Dataset file</Label>
            <FileUpload onChange={handleFileChange} />
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => setProjectDialogOpen(false)}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitDisabled}
          >
            {isExistingProjectMode ? "Add to project" : "Create project"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
