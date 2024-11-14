using System;
using UnityEngine;
using WebSocketSharp;
using WebSocketSharp.Server;
using Newtonsoft.Json.Linq; // Ensure Newtonsoft.Json is imported
using System.Threading.Tasks;

public class UnityWebSocketServerBehavior : WebSocketBehavior
{
    protected override void OnMessage(MessageEventArgs e)
    {
        Debug.Log($"Received Message: {e.Data}");
        HandleMessage(e.Data);
    }

    private void HandleMessage(string message)
    {
        try
        {
            JObject json = JObject.Parse(message);
            string action = json["action"]?.ToString();

            switch (action.ToLower())
            {
                case "import_model":
                    ImportModel(json);
                    break;
                case "place_model":
                    PlaceModel(json);
                    break;
                case "analyze_environment":
                    AnalyzeEnvironment();
                    break;
                default:
                    SendError($"Unknown action: {action}");
                    break;
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"Error parsing message: {ex.Message}");
            SendError("Invalid message format.");
        }
    }

    private void ImportModel(JObject json)
    {
        string modelPath = json["model_path"]?.ToString();
        if (string.IsNullOrEmpty(modelPath))
        {
            SendError("model_path is required for import_model action.");
            return;
        }

        // Implement model import logic here
        // Example: Load the model and add it to the scene

        // Placeholder implementation
        Debug.Log($"Importing model from {modelPath}");
        // TODO: Add actual model import code

        // Send success response
        JObject response = new JObject
        {
            ["status"] = "success",
            ["message"] = $"Model imported from {modelPath}."
        };
        Send(response.ToString());
    }

    private void PlaceModel(JObject json)
    {
        string modelName = json["model_name"]?.ToString();
        JObject coordinates = (JObject)json["coordinates"];

        if (string.IsNullOrEmpty(modelName) || coordinates == null)
        {
            SendError("model_name and coordinates are required for place_model action.");
            return;
        }

        float x = coordinates["x"]?.ToObject<float>() ?? 0f;
        float y = coordinates["y"]?.ToObject<float>() ?? 0f;
        float z = coordinates["z"]?.ToObject<float>() ?? 0f;

        // Implement model placement logic here
        // Example: Instantiate the model at the specified coordinates

        // Placeholder implementation
        Debug.Log($"Placing model '{modelName}' at ({x}, {y}, {z})");
        // TODO: Add actual model placement code

        // Send success response
        JObject response = new JObject
        {
            ["status"] = "success",
            ["message"] = $"Model '{modelName}' placed at ({x}, {y}, {z})."
        };
        Send(response.ToString());
    }

    private void AnalyzeEnvironment()
    {
        // Implement environment analysis logic here
        // Example: Scan the scene and generate an internal map

        // Placeholder implementation
        Debug.Log("Analyzing environment to create an internal map.");
        // TODO: Add actual analysis code

        // Example internal map
        JObject internalMap = new JObject
        {
            ["buildings"] = new JArray("Sheriff's Office", "Store", "Bank"),
            ["roads"] = new JArray("Main Street", "2nd Avenue"),
            ["parks"] = new JArray("Central Park")
        };

        // Send success response with internal map
        JObject response = new JObject
        {
            ["status"] = "success",
            ["internal_map"] = internalMap
        };
        Send(response.ToString());
    }

    private void SendError(string errorMessage)
    {
        JObject response = new JObject
        {
            ["status"] = "failure",
            ["error"] = errorMessage
        };
        Send(response.ToString());
    }
}

public class UnityWebSocketServer : MonoBehaviour
{
    private WebSocketServer wssv;
    public int port = 8080;

    void Start()
    {
        StartWebSocketServer();
    }

    void OnApplicationQuit()
    {
        StopWebSocketServer();
    }

    public void StartWebSocketServer()
    {
        wssv = new WebSocketServer(port);
        wssv.AddWebSocketService<UnityWebSocketServerBehavior>("/unity");
        wssv.Start();
        Debug.Log($"Unity WebSocket Server started on ws://localhost:{port}/unity");
    }

    public void StopWebSocketServer()
    {
        if (wssv != null)
        {
            wssv.Stop();
            Debug.Log("Unity WebSocket Server stopped.");
        }
    }
}