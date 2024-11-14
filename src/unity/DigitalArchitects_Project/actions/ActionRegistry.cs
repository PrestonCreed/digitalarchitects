public class ActionRegistry : MonoBehaviour
{
    private Dictionary<string, BaseAction> registeredActions = new Dictionary<string, BaseAction>();
    
    void Awake()
    {
        LoadActions();
    }
    
    private void LoadActions()
    {
        // Load all action ScriptableObjects from Assets/Actions folder
        var actions = Resources.LoadAll<BaseAction>("Actions");
        foreach (var action in actions)
        {
            RegisterAction(action);
        }
    }
    
    public void RegisterAction(BaseAction action)
    {
        if (!registeredActions.ContainsKey(action.actionId))
        {
            registeredActions[action.actionId] = action;
            Debug.Log($"Registered action: {action.actionId}");
        }
    }
    
    public async Task<ActionResult> ExecuteAction(string actionId, Dictionary<string, object> parameters)
    {
        if (registeredActions.TryGetValue(actionId, out BaseAction action))
        {
            if (action.ValidateParameters(parameters))
            {
                return await action.Execute(parameters);
            }
            return new ActionResult { success = false, error = "Invalid parameters" };
        }
        return new ActionResult { success = false, error = "Action not found" };
    }
}