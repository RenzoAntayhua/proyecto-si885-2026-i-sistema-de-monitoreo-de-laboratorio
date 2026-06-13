using System.Diagnostics;
using System.IO;
using System.ServiceProcess;
using System.Security.Principal;
using System.Xml.Linq;

namespace NetworkMonitorInstaller.Services
{
    /// <summary>
    /// Servicio para instalar y configurar el agente Wazuh en Windows.
    /// </summary>
    public class WazuhService
    {
        private readonly Action<string> _log;
        private const string OssecConfPath = @"C:\Program Files (x86)\ossec-agent\ossec.conf";
        private const string ServiceName = "WazuhSvc";

        public WazuhService(Action<string> log)
        {
            _log = log;
        }

        // ─────────────────────────────────────────────────────────────
        // HELPER: ¿el proceso actual YA corre como administrador real?
        // ─────────────────────────────────────────────────────────────
        public static bool EsAdministrador()
        {
            using var identity = WindowsIdentity.GetCurrent();
            var principal = new WindowsPrincipal(identity);
            return principal.IsInRole(WindowsBuiltInRole.Administrator);
        }

        /// <summary>
        /// Llama esto al arrancar la app. Si no es admin, se relanza
        /// a sí misma con "runas" y termina el proceso actual.
        /// </summary>
        public static void ReroutearSiNoEsAdmin()
        {
            if (EsAdministrador()) return;

            var psi = new ProcessStartInfo
            {
                FileName = Environment.ProcessPath
                           ?? System.Reflection.Assembly.GetExecutingAssembly().Location,
                UseShellExecute = true,
                Verb = "runas"   // Dispara el UAC prompt UNA SOLA VEZ al arrancar
            };

            try
            {
                Process.Start(psi);
            }
            catch (System.ComponentModel.Win32Exception)
            {
                // Usuario canceló el UAC
            }

            // Terminar el proceso no-elevado
            Environment.Exit(0);
        }

        /// <summary>
        /// Paso D: Instalar Wazuh Agent silenciosamente via msiexec.
        /// </summary>
        public async Task InstalarAgenteAsync(string msiPath, string managerIp)
        {
            var servicioExiste = ServiceController.GetServices()
                .Any(s => s.ServiceName.Equals(ServiceName, StringComparison.OrdinalIgnoreCase));

            if (servicioExiste)
            {
                _log("[OK] El agente de Wazuh ya está instalado. Saltando paso de instalación.");
                return;
            }

            _log("[...] Instalando Wazuh Agent...");

            var logPath = Path.Combine(Path.GetTempPath(), "wazuh_install.log");
            var args = $"/i \"{msiPath}\" /qn /l*v \"{logPath}\" " +
                       $"WAZUH_MANAGER=\"{managerIp}\" " +
                       $"WAZUH_REGISTRATION_SERVER=\"{managerIp}\" " +
                       $"WAZUH_PROTOCOL=\"TCP\"";

            var psi = new ProcessStartInfo
            {
                FileName = "msiexec.exe",
                Arguments = args,
                // Si ya somos admin (gracias a ReroutearSiNoEsAdmin),
                // podemos usar UseShellExecute = false y capturar output.
                // Si por alguna razón no somos admin, forzamos runas.
                UseShellExecute = !EsAdministrador(),
                Verb = EsAdministrador() ? "" : "runas",
                RedirectStandardOutput = EsAdministrador(),
                RedirectStandardError = EsAdministrador(),
                CreateNoWindow = EsAdministrador(),
            };

            using var process = Process.Start(psi)
                ?? throw new Exception("No se pudo iniciar msiexec.exe");

            await process.WaitForExitAsync();

            if (process.ExitCode != 0)
            {
                throw new Exception(
                    $"msiexec finalizó con código de error: {process.ExitCode}. " +
                    $"Revisa el log en: {logPath}"
                );
            }

            _log("[OK] Wazuh Agent instalado correctamente.");
        }

        /// <summary>
        /// Paso E: Modificar ossec.conf para añadir label con el laboratorio_id.
        /// FIX: Tomar ownership temporal del archivo si es necesario,
        /// o simplemente escribir directo (ya somos admin gracias a ReroutearSiNoEsAdmin).
        /// </summary>
        public void ConfigurarLabel(string laboratorioId)
        {
            _log("[...] Configurando label de laboratorio en ossec.conf...");

            if (!File.Exists(OssecConfPath))
            {
                throw new FileNotFoundException($"No se encontró ossec.conf en: {OssecConfPath}");
            }

            // FIX: Quitar atributo ReadOnly si lo tiene
            var attrs = File.GetAttributes(OssecConfPath);
            if (attrs.HasFlag(FileAttributes.ReadOnly))
            {
                File.SetAttributes(OssecConfPath, attrs & ~FileAttributes.ReadOnly);
            }

            XDocument doc;
            try
            {
                doc = XDocument.Load(OssecConfPath);
            }
            catch (Exception ex)
            {
                throw new Exception($"No se pudo leer ossec.conf: {ex.Message}");
            }

            var root = doc.Root ?? throw new Exception("ossec.conf no tiene elemento raíz.");

            var labelsElement = root.Element("labels");
            if (labelsElement == null)
            {
                labelsElement = new XElement("labels");
                root.Add(labelsElement);
            }

            var existingLabel = labelsElement.Elements("label")
                .FirstOrDefault(e => e.Attribute("key")?.Value == "laboratorio");

            if (existingLabel != null)
            {
                existingLabel.Value = laboratorioId;
            }
            else
            {
                labelsElement.Add(new XElement("label",
                    new XAttribute("key", "laboratorio"),
                    laboratorioId
                ));
            }

            // FIX: Guardar sin declaración XML y sin BOM para evitar error (line 0)
            var tempPath = OssecConfPath + ".tmp";
            try
            {
                var settings = new System.Xml.XmlWriterSettings
                {
                    OmitXmlDeclaration = true,
                    Indent = true,
                    Encoding = new System.Text.UTF8Encoding(false) // false = sin BOM
                };

                using (var writer = System.Xml.XmlWriter.Create(tempPath, settings))
                {
                    doc.Save(writer);
                }

                File.Copy(tempPath, OssecConfPath, overwrite: true);
                File.Delete(tempPath);
            }
            catch (UnauthorizedAccessException)
            {
                // Último recurso: intentar via cmd elevado
                File.Delete(tempPath);
                throw new UnauthorizedAccessException(
                    "Acceso denegado a ossec.conf. Asegúrate de que la aplicación " +
                    "se ejecuta como Administrador (clic derecho → Ejecutar como administrador)."
                );
            }

            _log($"[OK] Label configurado: laboratorio={laboratorioId}");
        }

        /// <summary>
        /// Paso F: Asegurar que Wazuh Agent lea el canal de Sysmon.
        /// </summary>
        public void ConfigurarSysmonChannel()
        {
            _log("[...] Configurando canal de Sysmon en ossec.conf...");
            if (!File.Exists(OssecConfPath)) return;

            var doc = XDocument.Load(OssecConfPath);
            var root = doc.Root ?? throw new Exception("ossec.conf no tiene elemento raíz.");

            // Buscar si ya existe la entrada de Sysmon
            var existingNode = root.Elements("localfile")
                .FirstOrDefault(e => e.Element("location")?.Value == "Microsoft-Windows-Sysmon/Operational");

            bool modificado = false;

            if (existingNode == null)
            {
                var sysmonNode = new XElement("localfile",
                    new XElement("location", "Microsoft-Windows-Sysmon/Operational"),
                    new XElement("log_format", "eventchannel")
                );
                root.Add(sysmonNode);
                modificado = true;
                _log("[OK] Canal de Sysmon añadido a ossec.conf.");
            }
            else
            {
                var formatNode = existingNode.Element("log_format");
                if (formatNode?.Value != "eventchannel")
                {
                    if (formatNode == null)
                    {
                        existingNode.Add(new XElement("log_format", "eventchannel"));
                    }
                    else
                    {
                        formatNode.Value = "eventchannel";
                    }
                    modificado = true;
                    _log("[OK] Formato del canal de Sysmon actualizado a 'eventchannel'.");
                }
                else
                {
                    _log("[OK] El canal de Sysmon ya estaba configurado correctamente.");
                }
            }

            if (modificado)
            {
                // Guardar usando la lógica segura
                var settings = new System.Xml.XmlWriterSettings
                {
                    OmitXmlDeclaration = true,
                    Indent = true,
                    Encoding = new System.Text.UTF8Encoding(false)
                };

                using (var writer = System.Xml.XmlWriter.Create(OssecConfPath, settings))
                {
                    doc.Save(writer);
                }
            }
        }

        /// <summary>
        /// Paso H: Aumentar los límites del buffer del agente para soportar alto tráfico de Sysmon.
        /// </summary>
        public void ConfigurarBuffer()
        {
            _log("[...] Optimizando buffer del agente para alto tráfico...");
            if (!File.Exists(OssecConfPath)) return;

            var doc = XDocument.Load(OssecConfPath);
            var root = doc.Root ?? throw new Exception("ossec.conf no tiene elemento raíz.");

            var bufferNode = root.Element("client_buffer");
            if (bufferNode == null)
            {
                bufferNode = new XElement("client_buffer");
                root.Add(bufferNode);
            }

            bufferNode.SetElementValue("disabled", "no");
            bufferNode.SetElementValue("queue_size", "100000");
            bufferNode.SetElementValue("events_per_second", "1000");

            // Guardar usando la lógica segura
            var settings = new System.Xml.XmlWriterSettings
            {
                OmitXmlDeclaration = true,
                Indent = true,
                Encoding = new System.Text.UTF8Encoding(false)
            };

            using (var writer = System.Xml.XmlWriter.Create(OssecConfPath, settings))
            {
                doc.Save(writer);
            }
            _log("[OK] Buffer optimizado: 100k eventos / 1000 EPS.");
        }

        /// <summary>
        /// Paso G: Reiniciar el servicio Wazuh.
        /// </summary>
        public async Task ReiniciarServicioAsync()
        {
            _log("[...] Reiniciando servicio Wazuh...");
            await EjecutarComandoAsync("net", $"stop {ServiceName}");
            await Task.Delay(2000);
            await EjecutarComandoAsync("net", $"start {ServiceName}");
            _log("[OK] Servicio Wazuh reiniciado correctamente.");
        }

        private async Task EjecutarComandoAsync(string fileName, string arguments)
        {
            var psi = new ProcessStartInfo
            {
                FileName = fileName,
                Arguments = arguments,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process != null)
            {
                await process.WaitForExitAsync();
            }
        }
    }
}