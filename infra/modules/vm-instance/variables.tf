variable "name" {
  description = "Name prefix applied to every resource."
  type        = string
}

variable "environment" {
  type    = string
  default = "staging"
}

variable "location" {
  description = "Azure region where resources are provisioned."
  type        = string
  default     = "swedencentral"
}

variable "vm_size" {
  description = "Standard_B2s_v2 (2 vCPU / 4 GiB) is optimal for k3s, ArgoCD and microservices under Azure for Students quota."
  type        = string
  default     = "Standard_B2s_v2"
}

variable "os_disk_size_gb" {
  type    = number
  default = 32
}

variable "admin_username" {
  type    = string
  default = "azureuser"
}

variable "ssh_public_key" {
  description = "Contents of the public key file, e.g. file(\"~/.ssh/orbit_vm_key.pub\")."
  type        = string
}

variable "ssh_allowed_cidrs" {
  description = "Address ranges allowed to reach SSH and the Kubernetes API."
  type        = list(string)

  validation {
    condition     = !contains(var.ssh_allowed_cidrs, "0.0.0.0/0")
    error_message = "Opening SSH and the Kubernetes API to the whole internet is not allowed."
  }
}

variable "k3s_version" {
  type    = string
  default = "v1.30.3+k3s1"
}

variable "tags" {
  type    = map(string)
  default = {}
}
