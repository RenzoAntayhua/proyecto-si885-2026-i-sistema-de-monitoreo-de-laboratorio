output "public_ip_address" {
  value       = azurerm_linux_virtual_machine.sysmon_vm.public_ip_address
  description = "La IP Pública del servidor para acceder al Dashboard y conectar los agentes Wazuh."
}
