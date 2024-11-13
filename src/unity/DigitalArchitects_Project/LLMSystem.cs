using UnityEngine;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using NetMQ;
using NetMQ.Sockets;
using Newtonsoft.Json;
using UnityEngine.SceneManagement;

namespace DigitalArchitect
{
    [Serializable]
    public class ProjectContext
    {
        public string theme { get; set; }
        public string time_period { get; set; }
        public List<string> existing_buildings { get; set; }
        public string environment { get; set; }
        public Dictionary<string, object> special_requirements { get; set; }

        public ProjectContext()
        {
            existing_buildings = new List<string>();
            special_requirements = new Dictionary<string, object>();
        }
    }

    [Serializable]
    public class ArchitecturalAnalysis
    {
        public string analysis { get; set; }               // Full text analysis from LLM
        public Dictionary<string, object> building_info { get; set; }
        public bool is_valid { get; set; } = true;
        public string error_message { get; set; }

        // Helper properties to access common sections of the analysis
        public string GetArchitecturalSection() => ExtractSection("Architectural Analysis");
        public string GetPlacementSection() => ExtractSection("Placement Considerations");
        public string GetRequirementsSection() => ExtractSection("Required Elements");
        public string GetConstructionSection() => ExtractSection("Construction Approach");
        public string GetAdditionalSection() => ExtractSection("Additional Considerations");

        private string ExtractSection(string sectionName)
        {
            // Simple section extraction - can be made more robust
            if (string.IsNullOrEmpty(analysis)) return string.Empty;
            
            int startIndex = analysis.IndexOf(sectionName);
            if (startIndex == -1) return string.Empty;
            
            int nextSection = analysis.IndexOf("\n\n", startIndex);
            if (nextSection == -1) nextSection = analysis.Length;
            
            return analysis.Substring(startIndex, nextSection - startIndex).Trim();
        }
    }

    public class DigitalArchitectInterface : MonoBehaviour
    {
        private RequestSocket client;
        private const string PYTHON_SERVER = "tcp://localhost:5555";
        private bool isConnected;
        
        [SerializeField] private bool debugMode = true;
        
        // Current project context
        private ProjectContext projectContext;

        private void Awake()
        {
            projectContext = new ProjectContext
            {
                theme = "western",  // Default theme - can be changed
                time_period = "1800s"
            };
        }

        private void Start()
        {
            ConnectToPython();
        }

        public void UpdateProjectContext(ProjectContext newContext)
        {
            projectContext = newContext;
        }

        private void ConnectToPython()
        {
            try
            {
                AsyncIO.ForceDotNet.Force();
                client = new RequestSocket();
                client.Connect(PYTHON_SERVER);
                isConnected = true;
                if(debugMode) Debug.Log("Connected to Digital Architect LLM Service");
            }
            catch (Exception e)
            {
                Debug.LogError($"Failed to connect to Digital Architect Service: {e.Message}");
                isConnected = false;
            }
        }

        public async Task<ArchitecturalAnalysis> RequestAnalysis(string userRequest, Dictionary<string, object> additionalContext = null)
        {
            if (!isConnected)
            {
                throw new InvalidOperationException("Not connected to Digital Architect Service");
            }

            try
            {
                // Combine project context with additional context
                var contextData = new Dictionary<string, object>
                {
                    { "theme", projectContext.theme },
                    { "time_period", projectContext.time_period },
                    { "existing_buildings", projectContext.existing_buildings },
                    { "environment", projectContext.environment },
                    { "special_requirements", projectContext.special_requirements }
                };

                if (additionalContext != null)
                {
                    foreach (var kvp in additionalContext)
                    {
                        contextData[kvp.Key] = kvp.Value;
                    }
                }

                // Format message with full context
                var messageData = new Dictionary<string, object>
                {
                    { "message", userRequest },
                    { "metadata", new Dictionary<string, object>
                        {
                            { "timestamp", DateTime.UtcNow.ToString("o") },
                            { "scene", SceneManager.GetActiveScene().name },
                            { "project_context", contextData }
                        }
                    }
                };

                string jsonRequest = JsonConvert.SerializeObject(messageData);
                if(debugMode) Debug.Log($"Sending request to Digital Architect: {jsonRequest}");
                
                client.SendFrame(jsonRequest);
                
                string jsonResponse = client.ReceiveFrameString();
                if(debugMode) Debug.Log($"Received analysis: {jsonResponse}");
                
                var analysis = JsonConvert.DeserializeObject<ArchitecturalAnalysis>(jsonResponse);
                
                return analysis ?? throw new Exception("Null response from Digital Architect");
            }
            catch (Exception ex)
            {
                Debug.LogError($"Error in Digital Architect communication: {ex.Message}");
                throw;
            }
        }

        private void OnDestroy()
        {
            try
            {
                client?.Dispose();
                NetMQConfig.Cleanup();
            }
            catch (Exception e)
            {
                Debug.LogError($"Error during cleanup: {e.Message}");
            }
        }
    }
}