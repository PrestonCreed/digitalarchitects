using UnityEngine;
using UnityEngine.UI;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using NetMQ;
using NetMQ.Sockets;
using Newtonsoft.Json;
using TMPro;

namespace DigitalArchitect
{
    public class DigitalArchitectManager : MonoBehaviour
    {
        [Header("Communication")]
        [SerializeField] private string serverAddress = "tcp://localhost:5555";
        [SerializeField] private bool debugMode = true;
        
        [Header("UI References")]
        [SerializeField] private TMP_InputField userInputField;
        [SerializeField] private Button sendButton;
        [SerializeField] private Transform messageContainer;
        [SerializeField] private GameObject userMessagePrefab;
        [SerializeField] private GameObject architectMessagePrefab;
        [SerializeField] private GameObject loadingIndicator;
        
        private RequestSocket client;
        private bool isConnected;
        private ProjectContext projectContext;

        private void Awake()
        {
            InitializeProjectContext();
            SetupUI();
        }

        private void Start()
        {
            ConnectToServer();
        }

        private void InitializeProjectContext()
        {
            projectContext = new ProjectContext
            {
                theme = "western",
                time_period = "1800s",
                existing_buildings = new List<string>(),
                environment = "desert_town",
                special_requirements = new Dictionary<string, object>()
            };
        }

        private void SetupUI()
        {
            sendButton.onClick.AddListener(async () => await HandleUserInput());
            userInputField.onSubmit.AddListener(async (text) => await HandleUserInput());
        }

        private void ConnectToServer()
        {
            try
            {
                AsyncIO.ForceDotNet.Force();
                client = new RequestSocket();
                client.Connect(serverAddress);
                isConnected = true;
                
                if (debugMode) Debug.Log("Connected to Digital Architect Server");
                
                // Enable UI
                sendButton.interactable = true;
                userInputField.interactable = true;
            }
            catch (Exception e)
            {
                Debug.LogError($"Failed to connect to server: {e.Message}");
                isConnected = false;
                
                // Disable UI
                sendButton.interactable = false;
                userInputField.interactable = false;
                
                // Show error in chat
                ShowErrorMessage("Failed to connect to Digital Architect service. Please try again later.");
            }
        }

        private async Task HandleUserInput()
        {
            if (!isConnected || string.IsNullOrEmpty(userInputField.text))
                return;

            string userMessage = userInputField.text;
            userInputField.text = string.Empty;

            // Show user message
            ShowUserMessage(userMessage);

            // Show loading indicator
            loadingIndicator.SetActive(true);

            try
            {
                var response = await SendRequest(userMessage);
                HandleArchitectResponse(response);
            }
            catch (Exception e)
            {
                Debug.LogError($"Error processing request: {e.Message}");
                ShowErrorMessage("Sorry, I encountered an error processing your request.");
            }
            finally
            {
                loadingIndicator.SetActive(false);
            }
        }

        private async Task<Dictionary<string, object>> SendRequest(string message)
        {
            if (!isConnected)
                throw new InvalidOperationException("Not connected to server");

            try
            {
                // Format message with context
                var messageData = new Dictionary<string, object>
                {
                    { "message", message },
                    { "metadata", new Dictionary<string, object>
                        {
                            { "timestamp", DateTime.UtcNow.ToString("o") },
                            { "scene", UnityEngine.SceneManagement.SceneManager.GetActiveScene().name },
                            { "project_context", projectContext }
                        }
                    }
                };

                string jsonRequest = JsonConvert.SerializeObject(messageData);
                if (debugMode) Debug.Log($"Sending: {jsonRequest}");

                client.SendFrame(jsonRequest);
                
                string jsonResponse = client.ReceiveFrameString();
                if (debugMode) Debug.Log($"Received: {jsonResponse}");

                return JsonConvert.DeserializeObject<Dictionary<string, object>>(jsonResponse);
            }
            catch (Exception ex)
            {
                Debug.LogError($"Error in request: {ex.Message}");
                throw;
            }
        }

        private void HandleArchitectResponse(Dictionary<string, object> response)
        {
            string responseType = response["type"].ToString();

            switch (responseType)
            {
                case "processing":
                    // Silent processing, no UI update needed
                    break;

                case "clarification":
                    ShowArchitectMessage(response["message"].ToString());
                    break;

                case "completion":
                    ShowArchitectMessage(response["message"].ToString());
                    // Handle any completion actions (like updating scene)
                    HandleCompletionActions(response);
                    break;

                case "error":
                    ShowErrorMessage(response["message"].ToString());
                    break;
            }
        }

        private void HandleCompletionActions(Dictionary<string, object> response)
        {
            // Handle any scene updates or other actions based on completion
            if (response.ContainsKey("actions"))
            {
                var actions = JsonConvert.DeserializeObject<List<Dictionary<string, object>>>(
                    response["actions"].ToString()
                );

                foreach (var action in actions)
                {
                    ExecuteAction(action);
                }
            }
        }

        private void ExecuteAction(Dictionary<string, object> action)
        {
            // Execute various scene actions based on architect response
            string actionType = action["type"].ToString();

            switch (actionType)
            {
                case "import_model":
                    // Handle model import
                    break;

                case "place_model":
                    // Handle model placement
                    break;

                case "update_scene":
                    // Handle scene updates
                    break;
            }
        }

        private void ShowUserMessage(string message)
        {
            var msgObj = Instantiate(userMessagePrefab, messageContainer);
            msgObj.GetComponentInChildren<TMP_Text>().text = message;
        }

        private void ShowArchitectMessage(string message)
        {
            var msgObj = Instantiate(architectMessagePrefab, messageContainer);
            msgObj.GetComponentInChildren<TMP_Text>().text = message;
        }

        private void ShowErrorMessage(string message)
        {
            var msgObj = Instantiate(architectMessagePrefab, messageContainer);
            var textComponent = msgObj.GetComponentInChildren<TMP_Text>();
            textComponent.text = message;
            textComponent.color = Color.red;
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