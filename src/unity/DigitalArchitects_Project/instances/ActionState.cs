using UnityEngine;
using System;
using System.Collections.Generic;
using Newtonsoft.Json;

[Serializable]
public class AgentActionState
{
    public string instanceId;
    public Vector3 position;
    public Quaternion rotation;
    public string currentAction;
    public Dictionary<string, object> actionParameters;
    public List<string> interactingObjects;
    public float lastUpdateTime;
    public Dictionary<string, object> customState;
}

public class ActionStateManager : MonoBehaviour
{
    private Dictionary<string, AgentActionState> agentStates = new Dictionary<string, AgentActionState>();
    private UnityWebSocketServer webSocketServer;

    void Awake()
    {
        webSocketServer = GetComponent<UnityWebSocketServer>();
    }

    public void UpdateAgentState(string instanceId, AgentActionState state)
    {
        agentStates[instanceId] = state;
        NotifyPythonOfStateChange(instanceId, state);
    }

    public AgentActionState GetAgentState(string instanceId)
    {
        return agentStates.ContainsKey(instanceId) ? agentStates[instanceId] : null;
    }

    private void NotifyPythonOfStateChange(string instanceId, AgentActionState state)
    {
        var stateUpdate = new Dictionary<string, object>
        {
            ["type"] = "action_state_update",
            ["instance_id"] = instanceId,
            ["state"] = new Dictionary<string, object>
            {
                ["position"] = new float[] { state.position.x, state.position.y, state.position.z },
                ["rotation"] = new float[] { state.rotation.eulerAngles.x, state.rotation.eulerAngles.y, state.rotation.eulerAngles.z },
                ["current_action"] = state.currentAction,
                ["action_parameters"] = state.actionParameters,
                ["interacting_objects"] = state.interactingObjects,
                ["last_update_time"] = state.lastUpdateTime,
                ["custom_state"] = state.customState
            }
        };

        webSocketServer.SendMessage(JsonConvert.SerializeObject(stateUpdate));
    }

    public void HandlePythonStateUpdate(Dictionary<string, object> stateUpdate)
    {
        string instanceId = stateUpdate["instance_id"].ToString();
        if (!agentStates.ContainsKey(instanceId))
        {
            agentStates[instanceId] = new AgentActionState { instanceId = instanceId };
        }

        var state = agentStates[instanceId];
        var updates = (Dictionary<string, object>)stateUpdate["state"];

        // Update relevant action state based on Python's update
        foreach (var kvp in updates)
        {
            switch (kvp.Key)
            {
                case "target_position":
                    // Handle movement commands
                    var pos = (float[])kvp.Value;
                    StartCoroutine(MoveAgentTo(instanceId, new Vector3(pos[0], pos[1], pos[2])));
                    break;
                case "action":
                    // Handle new action commands
                    state.currentAction = kvp.Value.ToString();
                    ExecuteAction(instanceId, kvp.Value.ToString(), updates.ContainsKey("parameters") ? (Dictionary<string, object>)updates["parameters"] : null);
                    break;
                // Add other state update handlers
            }
        }
    }

    private IEnumerator MoveAgentTo(string instanceId, Vector3 targetPosition)
    {
        var state = agentStates[instanceId];
        float speed = 5f; // Adjust as needed

        while (Vector3.Distance(state.position, targetPosition) > 0.1f)
        {
            state.position = Vector3.MoveTowards(state.position, targetPosition, speed * Time.deltaTime);
            UpdateAgentState(instanceId, state);
            yield return null;
        }
    }

    private void ExecuteAction(string instanceId, string action, Dictionary<string, object> parameters)
    {
        // Implement action execution logic
        Debug.Log($"Executing action {action} for agent {instanceId}");
    }
}