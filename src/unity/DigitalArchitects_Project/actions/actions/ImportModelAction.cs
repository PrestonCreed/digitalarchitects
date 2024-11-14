[CreateAssetMenu(fileName = "ImportModelAction", menuName = "Actions/Import Model")]
public class ImportModelAction : BaseAction
{
    public override async Task<ActionResult> Execute(Dictionary<string, object> parameters)
    {
        // Implementation
        string modelPath = parameters["model_path"].ToString();
        
        // Actual Unity-specific implementation
        var model = await LoadModel(modelPath);
        // etc...
        
        return new ActionResult { success = true, data = new Dictionary<string, object>() };
    }
    
    public override bool ValidateParameters(Dictionary<string, object> parameters)
    {
        return parameters.ContainsKey("model_path");
    }
}