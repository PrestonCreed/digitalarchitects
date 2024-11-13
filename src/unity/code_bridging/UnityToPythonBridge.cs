using UnityEngine;
using System;
using System.Threading.Tasks;
using NetMQ;
using NetMQ.Sockets;
using Newtonsoft.Json;

public class PythonBridge : MonoBehaviour
{
    private RequestSocket client;
    private const string SERVER_ADDRESS = "tcp://localhost:5555";

    private void Start()
    {
        InitializeConnection();
    }

    private void InitializeConnection()
    {
        AsyncIO.ForceDotNet.Force();
        client = new RequestSocket();
        client.Connect(SERVER_ADDRESS);
    }

    public async Task<AgentResponse> SendRequest(AgentRequest request)
    {
        try
        {
            string jsonRequest = JsonConvert.SerializeObject(request);
            client.SendFrame(jsonRequest);
            
            string jsonResponse = client.ReceiveFrameString();
            return JsonConvert.DeserializeObject<AgentResponse>(jsonResponse);
        }
        catch (Exception ex)
        {
            Debug.LogError($"Error communicating with Python agent: {ex.Message}");
            return new AgentResponse { Success = false, Error = ex.Message };
        }
    }

    private void OnDestroy()
    {
        client?.Dispose();
        NetMQConfig.Cleanup();
    }
}

public class AgentRequest
{
    public string Type { get; set; }
    public string Message { get; set; }
    public Dictionary<string, object> Parameters { get; set; }
}

public class AgentResponse
{
    public bool Success { get; set; }
    public string Error { get; set; }
    public Dictionary<string, object> Data { get; set; }
}