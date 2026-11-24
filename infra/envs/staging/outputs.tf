# Surface the module outputs at the environment level so callers
# (e.g. the Terraform plan workflow or a human) can read the VM's
# public IP and SSH command without having to dig into the state file.

output "public_ip" {
  description = "Public IP address of the staging VM."
  value       = module.orbit_vm.public_ip
}

output "vm_name" {
  description = "Name of the staging virtual machine."
  value       = module.orbit_vm.vm_name
}

output "resource_group_name" {
  description = "Azure resource group that contains all staging resources."
  value       = module.orbit_vm.resource_group_name
}

output "ssh_connection_string" {
  description = "Ready-to-use SSH command for the staging VM."
  value       = module.orbit_vm.ssh_connection_string
}
