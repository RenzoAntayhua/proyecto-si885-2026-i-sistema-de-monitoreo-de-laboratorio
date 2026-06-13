using System.Text.Json.Serialization;

namespace NetworkMonitorInstaller.Models
{
    public class Laboratorio
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;

        [JsonPropertyName("nombre")]
        public string Nombre { get; set; } = string.Empty;

        [JsonPropertyName("descripcion")]
        public string? Descripcion { get; set; }

        [JsonPropertyName("total_computadoras")]
        public int TotalComputadoras { get; set; }

        /// <summary>Display name for ComboBox binding.</summary>
        public string DisplayName => $"{Nombre} ({TotalComputadoras} PCs)";
    }

    public class ComputadoraRegistro
    {
        [JsonPropertyName("hostname")]
        public string Hostname { get; set; } = string.Empty;

        [JsonPropertyName("laboratorio_id")]
        public string LaboratorioId { get; set; } = string.Empty;

        [JsonPropertyName("ip_local")]
        public string? IpLocal { get; set; }
    }
}
