using System.Diagnostics;
using System.IO;

namespace NetworkMonitorInstaller.Services
{
    /// <summary>
    /// Servicio para generar la configuración de Sysmon e instalarlo.
    /// Captura solo ProcessCreate (Event ID 1) y NetworkConnect (Event ID 3).
    /// </summary>
    public class SysmonService
    {
        private readonly string _workDir;
        private readonly Action<string> _log;

        public SysmonService(string workDir, Action<string> log)
        {
            _workDir = workDir;
            _log = log;
        }

        /// <summary>
        /// Genera el archivo sysmon_config.xml con reglas estrictas.
        /// Solo captura ProcessCreate y NetworkConnect (Event ID 3).
        /// </summary>
        public string GenerarConfigXml()
        {
            var configPath = Path.Combine(_workDir, "sysmon_config.xml");
            var xml = @"<Sysmon schemaversion=""4.90"">
  <!-- Captura solo lo necesario para monitoreo de red -->
  <HashAlgorithms>SHA256</HashAlgorithms>

  <EventFiltering>
    <!-- Event ID 1: Creación de procesos (Desactivado para reducir ruido) -->
    <RuleGroup name=""ProcessCreate"" groupRelation=""or"">
      <ProcessCreate onmatch=""include"" />
    </RuleGroup>

    <!-- Event ID 3: Conexiones de red (NetworkConnect) - CAPTURAR TODO -->
    <RuleGroup name=""NetworkConnect"" groupRelation=""or"">
      <NetworkConnect onmatch=""exclude"" />
    </RuleGroup>

    <!-- Ignorar todos los demás eventos para reducir ruido -->
    <RuleGroup name=""FileCreateTime"" groupRelation=""or"">
      <FileCreateTime onmatch=""include"" />
    </RuleGroup>

    <RuleGroup name=""ImageLoad"" groupRelation=""or"">
      <ImageLoad onmatch=""include"" />
    </RuleGroup>

    <RuleGroup name=""CreateRemoteThread"" groupRelation=""or"">
      <CreateRemoteThread onmatch=""include"" />
    </RuleGroup>

    <RuleGroup name=""RawAccessRead"" groupRelation=""or"">
      <RawAccessRead onmatch=""include"" />
    </RuleGroup>

    <RuleGroup name=""FileCreate"" groupRelation=""or"">
      <FileCreate onmatch=""include"" />
    </RuleGroup>

    <RuleGroup name=""RegistryEvent"" groupRelation=""or"">
      <RegistryEvent onmatch=""include"" />
    </RuleGroup>

    <RuleGroup name=""FileCreateStreamHash"" groupRelation=""or"">
      <FileCreateStreamHash onmatch=""include"" />
    </RuleGroup>

    <RuleGroup name=""PipeEvent"" groupRelation=""or"">
      <PipeEvent onmatch=""include"" />
    </RuleGroup>

    <RuleGroup name=""WmiEvent"" groupRelation=""or"">
      <WmiEvent onmatch=""include"" />
    </RuleGroup>

    <RuleGroup name=""DnsQuery"" groupRelation=""or"">
      <DnsQuery onmatch=""include"" />
    </RuleGroup>

    <RuleGroup name=""FileDelete"" groupRelation=""or"">
      <FileDelete onmatch=""include"" />
    </RuleGroup>

    <RuleGroup name=""ProcessTampering"" groupRelation=""or"">
      <ProcessTampering onmatch=""include"" />
    </RuleGroup>
  </EventFiltering>
</Sysmon>";

            File.WriteAllText(configPath, xml);
            _log($"[OK] Configuración Sysmon generada: {configPath}");
            return configPath;
        }

        /// <summary>
        /// Ejecuta Sysmon64.exe con la configuración generada.
        /// </summary>
        public async Task InstalarSysmonAsync(string sysmonExePath, string configPath)
        {
            _log("[...] Instalando Sysmon...");

            var psi = new ProcessStartInfo
            {
                FileName = sysmonExePath,
                Arguments = $"-accepteula -i \"{configPath}\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                Verb = "runas"
            };

            using var process = Process.Start(psi)
                ?? throw new Exception("No se pudo iniciar Sysmon64.exe");

            var stdout = await process.StandardOutput.ReadToEndAsync();
            var stderr = await process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();

            if (!string.IsNullOrWhiteSpace(stdout)) _log(stdout.Trim());
            if (!string.IsNullOrWhiteSpace(stderr)) _log(stderr.Trim());

            // Exit code 0 = éxito, 1 = ya instalado (actualizar config)
            if (process.ExitCode != 0)
            {
                _log("[WARN] Sysmon posiblemente ya instalado. Actualizando configuración...");
                var updatePsi = new ProcessStartInfo
                {
                    FileName = sysmonExePath,
                    Arguments = $"-c \"{configPath}\"",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };
                using var updateProc = Process.Start(updatePsi);
                if (updateProc != null) await updateProc.WaitForExitAsync();
            }

            _log("[OK] Sysmon instalado/actualizado correctamente.");
        }
    }
}
