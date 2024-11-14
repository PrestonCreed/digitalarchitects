using UnityEngine;
using System;
using System.Threading.Tasks;
using System.Collections.Generic;
using WebSocketSharp;
using WebSocketSharp.Server;
using Newtonsoft.Json.Linq;

public class EnvironmentAction
{
    public string actionType;
    public Dictionary<string, object> parameters;
    public string agentId;
    public string[] requiredPermissions;
}

public class EnvironmentController : MonoBehaviour
{
    [Header("Environment Settings")]
    [SerializeField] private bool allowAutonomousAgents = true;
    [SerializeField] private string[] enabledActions;
    
    [Header("Debug")]
    [SerializeField] private bool debugMode = true;

    private WebSocketServer wssv;
    private Dictionary<string, AgentPermissions> agentPermissions = new Dictionary<string, AgentPermissions>();

    #region Environment State Management
    private Dictionary<string, object> environmentState = new Dictionary<string, object>();
    private List<EnvironmentObserver> stateObservers = new List<EnvironmentObserver>();

    public void UpdateEnvironmentState(string key, object value)
    {
        environmentState[key] = value;
        NotifyStateObservers(key, value);
    }

    private void NotifyStateObservers(string key, object value)
    {
        foreach (var observer in stateObservers)
        {
            observer.OnStateChanged(key, value);
        }
    }
    #endregion

    #region Action Handling
    public async Task<ActionResult> ExecuteAction(EnvironmentAction action)
    {
        try
        {
            // Validate permissions
            if (!ValidatePermissions(action))
            {
                return new ActionResult { success = false, error = "Insufficient permissions" };
            }

            // Execute based on action type
            switch (action.actionType)
            {
                case "import_model":
                    return await ImportModel(action.parameters);
                case "place_model":
                    return await PlaceModel(action.parameters);
                case "modify_terrain":
                    return await ModifyTerrain(action.parameters);
                case "analyze_area":
                    return await AnalyzeArea(action.parameters);
                default:
                    return new ActionResult { success = false, error = "Unknown action type" };
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Error executing action: {e.Message}");
            return new ActionResult { success = false, error = e.Message };
        }
    }

    private async Task<ActionResult> ImportModel(Dictionary<string, object> parameters)
    {
        try
        {
            string modelPath = parameters["model_path"].ToString();
            
            // Load model from Assets
            GameObject modelPrefab = await LoadModelAsync(modelPath);
            if (modelPrefab == null)
                return new ActionResult { success = false, error = "Failed to load model" };

            // Register model in environment
            string modelId = Guid.NewGuid().ToString();
            environmentState[$"model_{modelId}"] = modelPath;

            return new ActionResult 
            { 
                success = true, 
                data = new Dictionary<string, object> { { "model_id", modelId } }
            };
        }
        catch (Exception e)
        {
            return new ActionResult { success = false, error = e.Message };
        }
    }

    private async Task<ActionResult> PlaceModel(Dictionary<string, object> parameters)
    {
        try
        {
            string modelId = parameters["model_id"].ToString();
            Vector3 position = JsonToVector3(parameters["position"]);
            Quaternion rotation = JsonToQuaternion(parameters["rotation"]);

            // Get model from environment
            string modelPath = environmentState[$"model_{modelId}"].ToString();
            GameObject modelPrefab = await LoadModelAsync(modelPath);

            // Instantiate and place
            GameObject instance = Instantiate(modelPrefab, position, rotation);
            
            // Snap to terrain if needed
            if (parameters.ContainsKey("snap_to_terrain") && (bool)parameters["snap_to_terrain"])
            {
                SnapToTerrain(instance);
            }

            // Register placement in environment state
            string placementId = Guid.NewGuid().ToString();
            environmentState[$"placement_{placementId}"] = new Dictionary<string, object>
            {
                { "model_id", modelId },
                { "position", position },
                { "rotation", rotation }
            };

            return new ActionResult 
            { 
                success = true,
                data = new Dictionary<string, object> { { "placement_id", placementId } }
            };
        }
        catch (Exception e)
        {
            return new ActionResult { success = false, error = e.Message };
        }
    }

    private void SnapToTerrain(GameObject obj)
    {
        RaycastHit hit;
        var pos = obj.transform.position;
        if (Physics.Raycast(pos + Vector3.up * 100f, Vector3.down, out hit))
        {
            obj.transform.position = hit.point;
        }
    }

    #endregion

    #region Helper Methods
    private Vector3 JsonToVector3(object vectorData)
    {
        var dict = vectorData as Dictionary<string, object>;
        return new Vector3(
            Convert.ToSingle(dict["x"]),
            Convert.ToSingle(dict["y"]),
            Convert.ToSingle(dict["z"])
        );
    }

    private Quaternion JsonToQuaternion(object rotationData)
    {
        var dict = rotationData as Dictionary<string, object>;
        return Quaternion.Euler(
            Convert.ToSingle(dict["x"]),
            Convert.ToSingle(dict["y"]),
            Convert.ToSingle(dict["z"])
        );
    }

    private async Task<GameObject> LoadModelAsync(string path)
    {
        // Implementation depends on your asset management system
        return null; // Placeholder
    }
    #endregion

    #region Permission Management
    private bool ValidatePermissions(EnvironmentAction action)
    {
        if (!agentPermissions.ContainsKey(action.agentId))
            return false;

        var permissions = agentPermissions[action.agentId];
        foreach (var requiredPermission in action.requiredPermissions)
        {
            if (!permissions.HasPermission(requiredPermission))
                return false;
        }

        return true;
    }
    #endregion
}

public class ActionResult
{
    public bool success;
    public string error;
    public Dictionary<string, object> data;
}

public class AgentPermissions
{
    private HashSet<string> permissions = new HashSet<string>();

    public bool HasPermission(string permission)
    {
        return permissions.Contains(permission);
    }

    public void GrantPermission(string permission)
    {
        permissions.Add(permission);
    }

    public void RevokePermission(string permission)
    {
        permissions.Remove(permission);
    }
}

public interface EnvironmentObserver
{
    void OnStateChanged(string key, object value);
}