using System.IO;
using System.Net.Http;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Windows;
using NetworkMonitorInstaller.Models;
using NetworkMonitorInstaller.Services;

namespace NetworkMonitorInstaller
{
    public partial class MainWindow : Window
    {
        private List<Laboratorio> _laboratorios = new();
        private readonly string _workDir;

        public MainWindow()
        {
            WazuhService.ReroutearSiNoEsAdmin();
            InitializeComponent();
            _workDir = Path.Combine(Path.GetTempPath(), "NetMonitorInstaller");
            Directory.CreateDirectory(_workDir);
            Log("Instalador iniciado. Configure los parámetros y haga clic en 'Instalar'.");
        }

        // ── Cargar laboratorios ────────────────────────────────────────────
        private async void BtnRefreshLabs_Click(object sender, RoutedEventArgs e)
        {
            var apiUrl = TxtApiUrl.Text.Trim();
            if (string.IsNullOrEmpty(apiUrl))
            {
                Log("[ERROR] Ingrese la URL del servidor API.");
                return;
            }

            try
            {
                Log("[...] Conectando con la API...");
                var api = new ApiService(apiUrl);
                _laboratorios = await api.GetLaboratoriosAsync();
                CmbLaboratorios.ItemsSource = _laboratorios;

                if (_laboratorios.Count > 0)
                {
                    CmbLaboratorios.SelectedIndex = 0;
                    Log($"[OK] {_laboratorios.Count} laboratorio(s) cargados.");
                }
                else
                {
                    Log("[WARN] No hay laboratorios registrados. Cree uno desde el Dashboard.");
                }
            }
            catch (Exception ex)
            {
                Log($"[ERROR] No se pudo conectar: {ex.Message}");
            }
        }

        // ── Proceso de instalación completo (Pasos A-G) ───────────────────
        private async void BtnInstalar_Click(object sender, RoutedEventArgs e)
        {
            // Validaciones
            var apiUrl = TxtApiUrl.Text.Trim();
            var vpsIp = TxtVpsIp.Text.Trim();
            var labSeleccionado = CmbLaboratorios.SelectedItem as Laboratorio;

            if (string.IsNullOrEmpty(apiUrl) || string.IsNullOrEmpty(vpsIp))
            {
                Log("[ERROR] Complete todos los campos requeridos.");
                return;
            }
            if (labSeleccionado == null)
            {
                Log("[ERROR] Seleccione un laboratorio.");
                return;
            }

            BtnInstalar.IsEnabled = false;
            ProgressBar.Value = 0;

            try
            {
                var sysmonPath = Path.Combine(_workDir, "Sysmon64.exe");
                var msiPath = Path.Combine(_workDir, "wazuh-agent.msi");

                // ── Paso A: Descargar Sysmon64.exe y wazuh-agent.msi ───────
                Log("\n═══ PASO A: Descargando archivos... ═══");
                await DescargarArchivoAsync($"http://{vpsIp}/downloads/Sysmon64.exe", sysmonPath);
                ProgressBar.Value = 14;
                await DescargarArchivoAsync($"http://{vpsIp}/downloads/wazuh-agent.msi", msiPath);
                ProgressBar.Value = 28;

                // ── Paso B: Generar sysmon_config.xml ──────────────────────
                Log("\n═══ PASO B: Generando configuración Sysmon... ═══");
                var sysmonSvc = new SysmonService(_workDir, Log);
                var configPath = sysmonSvc.GenerarConfigXml();
                ProgressBar.Value = 38;

                // ── Paso C: Ejecutar Sysmon ────────────────────────────────
                Log("\n═══ PASO C: Instalando Sysmon... ═══");
                await sysmonSvc.InstalarSysmonAsync(sysmonPath, configPath);
                ProgressBar.Value = 52;

                // ── Paso D: Instalar Wazuh Agent ───────────────────────────
                Log("\n═══ PASO D: Instalando Wazuh Agent... ═══");
                var wazuhSvc = new WazuhService(Log);
                await wazuhSvc.InstalarAgenteAsync(msiPath, vpsIp);
                ProgressBar.Value = 68;

                // ── Paso E: Configurar ossec.conf con label ────────────────
                Log("\n═══ PASO E: Configurando label de laboratorio... ═══");
                await Task.Delay(2000); // Esperar a que el agente complete la instalación
                wazuhSvc.ConfigurarLabel(labSeleccionado.Id);
                ProgressBar.Value = 78;

                // ── Paso F: Registrar PC en la API ─────────────────────────
                Log("\n═══ PASO F: Registrando PC en la API... ═══");
                var hostname = Environment.MachineName;
                var ipLocal = ObtenerIpLocal();
                var api = new ApiService(apiUrl);
                await api.RegistrarComputadoraAsync(hostname, labSeleccionado.Id, ipLocal);
                Log($"[OK] PC registrada: {hostname} ({ipLocal}) → {labSeleccionado.Nombre}");
                ProgressBar.Value = 90;

                // ── Paso G: Reiniciar servicio Wazuh ═══
                Log("\n═══ PASO G: Configurando y reiniciando Wazuh... ═══");
                wazuhSvc.ConfigurarSysmonChannel();
                wazuhSvc.ConfigurarBuffer();
                await wazuhSvc.ReiniciarServicioAsync();
                ProgressBar.Value = 100;

                Log("\n✅ ═══ INSTALACIÓN COMPLETADA EXITOSAMENTE ═══");
                Log($"   Hostname: {hostname}");
                Log($"   IP Local: {ipLocal}");
                Log($"   Laboratorio: {labSeleccionado.Nombre}");
                Log($"   Wazuh Manager: {vpsIp}");

                MessageBox.Show(
                    $"Instalación completada.\n\nPC: {hostname}\nLaboratorio: {labSeleccionado.Nombre}",
                    "Éxito", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                Log($"\n❌ [ERROR] {ex.Message}");
                MessageBox.Show($"Error durante la instalación:\n{ex.Message}",
                    "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                BtnInstalar.IsEnabled = true;
            }
        }

        // ── Utilidades ─────────────────────────────────────────────────────

        private async Task DescargarArchivoAsync(string url, string destino)
        {
            Log($"[...] Descargando: {url}");
            using var client = new HttpClient { Timeout = TimeSpan.FromMinutes(10) };
            using var response = await client.GetAsync(url, HttpCompletionOption.ResponseHeadersRead);
            response.EnsureSuccessStatusCode();
            await using var fs = new FileStream(destino, FileMode.Create, FileAccess.Write, FileShare.None);
            await response.Content.CopyToAsync(fs);
            Log($"[OK] Descargado: {Path.GetFileName(destino)}");
        }

        private static string ObtenerIpLocal()
        {
            try
            {
                foreach (var ni in NetworkInterface.GetAllNetworkInterfaces())
                {
                    if (ni.OperationalStatus != OperationalStatus.Up) continue;
                    if (ni.NetworkInterfaceType == NetworkInterfaceType.Loopback) continue;

                    foreach (var addr in ni.GetIPProperties().UnicastAddresses)
                    {
                        if (addr.Address.AddressFamily == AddressFamily.InterNetwork)
                            return addr.Address.ToString();
                    }
                }
            }
            catch { }
            return "0.0.0.0";
        }

        private void Log(string message)
        {
            Dispatcher.Invoke(() =>
            {
                TxtLog.Text += $"[{DateTime.Now:HH:mm:ss}] {message}\n";
                TxtLog.ScrollToEnd();
            });
        }
    }
}
