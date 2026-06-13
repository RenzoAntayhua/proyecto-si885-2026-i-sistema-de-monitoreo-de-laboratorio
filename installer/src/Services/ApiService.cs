using System.Net.Http;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using NetworkMonitorInstaller.Models;

namespace NetworkMonitorInstaller.Services
{
    /// <summary>
    /// Servicio de comunicación con la API REST del servidor central.
    /// </summary>
    public class ApiService
    {
        private readonly HttpClient _client;

        public ApiService(string apiBaseUrl)
        {
            _client = new HttpClient
            {
                BaseAddress = new Uri(apiBaseUrl.TrimEnd('/')),
                Timeout = TimeSpan.FromSeconds(30)
            };
        }

        /// <summary>
        /// Obtiene la lista de laboratorios desde GET /api/laboratorios/.
        /// </summary>
        public async Task<List<Laboratorio>> GetLaboratoriosAsync()
        {
            var response = await _client.GetAsync("/api/laboratorios/");
            response.EnsureSuccessStatusCode();
            var labs = await response.Content.ReadFromJsonAsync<List<Laboratorio>>();
            return labs ?? new List<Laboratorio>();
        }

        /// <summary>
        /// Registra una nueva computadora via POST /api/computadoras/.
        /// </summary>
        public async Task RegistrarComputadoraAsync(string hostname, string laboratorioId, string ipLocal)
        {
            var payload = new ComputadoraRegistro
            {
                Hostname = hostname,
                LaboratorioId = laboratorioId,
                IpLocal = ipLocal
            };

            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var response = await _client.PostAsync("/api/computadoras/", content);
            response.EnsureSuccessStatusCode();
        }
    }
}
