variable "resource_group_name" {
  type        = string
  description = "Nombre del Resource Group en Azure"
  default     = "rg-sysmon-telemetry"
}

variable "location" {
  type        = string
  description = "Región de Azure donde se desplegará (ej. eastus)"
  default     = "eastus2"
}

variable "vm_size" {
  type        = string
  description = "Tamaño de la Máquina Virtual (Standard_B2s es ideal para la capa gratuita/estudiante y soporta ELK/Postgres)"
  default     = "Standard_B2s"
}

variable "admin_username" {
  type        = string
  description = "Usuario administrador de la máquina Ubuntu"
  default     = "sysmonadmin"
}
