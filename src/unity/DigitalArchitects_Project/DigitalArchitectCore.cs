using UnityEngine;
using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;

public class DigitalArchitectCore : MonoBehaviour
{
    [Header("Component References")]
    [SerializeField] private UnityWebSocketServer webSocketServer;
    [SerializeField] private EnvironmentController environmentController;
    [SerializeField] private DigitalArchitectManager uiManager;
    [SerializeField] private ActionRegistry actionRegistry;

    [Header("Debug Settings")]
    [SerializeField] private bool debugMode = true;
    [SerializeField] private bool mockPythonResponses = false; // For testing without Python

    private void Awake()
    {
        ValidateComponents();
        SetupEventListeners();
    }

    private void ValidateComponents()
    {
        if (webSocketServer == null) webSocketServer = GetComponent<UnityWebSocketServer>();
        if (environmentController == null) environmentController = GetComponent<EnvironmentController>();
        if (uiManager == null) uiManager = GetComponent<DigitalArchitectManager>();
        if (actionRegistry == null) actionRegistry = GetComponent<ActionRegistry>();

        if (webSocketServer == null || environmentController == null || 
            uiManager == null || actionRegistry == null)
        {
            Debug.LogError("Missing required components on DigitalArchitectCore!");
        }
    }

    private void SetupEventListeners()
    {
        // Connect WebSocket messages to Environment Controller
        webSocketServer.OnMessageReceived += HandleWebSocketMessage;
        
        // Connect UI events to WebSocket
        uiManager.OnUserMessageSent += HandleUserMessage;
        
        // Connect Environment changes to UI
        environmentController.OnEnvironmentChanged += HandleEnvironmentChange;
    }

    private async void HandleWebSocketMessage(string message)
    {
        try
        {
            JObject json = JObject.Parse(message);
            string actionType = json["action"]?.ToString();

            // Log incoming message if in debug mode
            if (debugMode) Debug.Log($"Received message: {message}");

            // Handle message based on type
            switch (actionType)
            {
                case "chat_response":
                    uiManager.ShowAgentMessage(json["message"].ToString());
                    break;

                case "environment_action":
                    var action = new EnvironmentAction
                    {
                        actionType = json["actionDetails"]["type"].ToString(),
                        parameters = json["actionDetails"]["parameters"].ToObject<Dictionary<string, object>>(),
                        agentId = json["agentId"].ToString()
                    };
                    var result = await environmentController.ExecuteAction(action);
                    SendActionResult(result);
                    break;

                default:
                    Debug.LogWarning($"Unknown action type: {actionType}");
                    break;
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Error handling WebSocket message: {e.Message}");
        }
    }

    private void HandleUserMessage(string message)
    {
        if (mockPythonResponses)
        {
            // For testing without Python connection
            MockPythonResponse(message);
            return;
        }

        // Format and send message through WebSocket
        var messageData = new JObject
        {
            ["type"] = "user_message",
            ["content"] = message,
            ["timestamp"] = DateTime.UtcNow.ToString("o")
        };

        webSocketServer.SendMessage(messageData.ToString());
    }

    private void HandleEnvironmentChange(string key, object value)
    {
        // Update UI with environment changes
        uiManager.UpdateEnvironmentDisplay(key, value);

        // Notify Python about environment changes
        var changeData = new JObject
        {
            ["type"] = "environment_update",
            ["key"] = key,
            ["value"] = JToken.FromObject(value)
        };

        webSocketServer.SendMessage(changeData.ToString());
    }

    private void SendActionResult(ActionResult result)
    {
        var resultData = new JObject
        {
            ["type"] = "action_result",
            ["success"] = result.success,
            ["data"] = result.data != null ? JToken.FromObject(result.data) : null,
            ["error"] = result.error
        };

        webSocketServer.SendMessage(resultData.ToString());
    }

    private void MockPythonResponse(string userMessage)
    {
        // For testing without Python connection
        string mockResponse = $"Mock response to: {userMessage}";
        uiManager.ShowAgentMessage(mockResponse);
    }

    // Test methods
    public void TestWebSocketConnection()
    {
        var testMessage = new JObject
        {
            ["type"] = "test",
            ["message"] = "Testing connection"
        };
        webSocketServer.SendMessage(testMessage.ToString());
    }

    public async void TestEnvironmentAction()
    {
        var testAction = new EnvironmentAction
        {
            actionType = "place_model",
            parameters = new Dictionary<string, object>
            {
                ["model_name"] = "TestCube",
                ["position"] = new Dictionary<string, object>
                {
                    ["x"] = 0f,
                    ["y"] = 0f,
                    ["z"] = 0f
                }
            }
        };

        await environmentController.ExecuteAction(testAction);
    }

    private void OnDestroy()
    {
        // Cleanup event listeners
        if (webSocketServer != null) webSocketServer.OnMessageReceived -= HandleWebSocketMessage;
        if (uiManager != null) uiManager.OnUserMessageSent -= HandleUserMessage;
        if (environmentController != null) environmentController.OnEnvironmentChanged -= HandleEnvironmentChange;
    }
}