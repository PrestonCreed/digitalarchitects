private void PlaceModel(JObject json)
{
    JObject parameters = (JObject)json["parameters"];
    if (parameters == null)
    {
        SendError("parameters are required for place_model action.");
        return;
    }

    string modelName = parameters["model_name"]?.ToString();
    JObject positionJson = (JObject)parameters["position"];
    JObject rotationJson = (JObject)parameters["rotation"];

    if (string.IsNullOrEmpty(modelName) || positionJson == null || rotationJson == null)
    {
        SendError("model_name, position, and rotation are required for place_model action.");
        return;
    }

    Vector3 position = new Vector3(
        positionJson["x"]?.ToObject<float>() ?? 0f,
        positionJson["y"]?.ToObject<float>() ?? 0f,
        positionJson["z"]?.ToObject<float>() ?? 0f
    );

    Vector3 rotationEuler = new Vector3(
        rotationJson["x"]?.ToObject<float>() ?? 0f,
        rotationJson["y"]?.ToObject<float>() ?? 0f,
        rotationJson["z"]?.ToObject<float>() ?? 0f
    );

    Quaternion rotation = Quaternion.Euler(rotationEuler);

    // Load the model from Resources
    GameObject modelPrefab = Resources.Load<GameObject>($"Models/{modelName}");
    if (modelPrefab == null)
    {
        SendError($"Model '{modelName}' not found.");
        return;
    }

    // Instantiate the model at the specified position and rotation
    GameObject instance = Instantiate(modelPrefab, position, rotation);

    // Optionally, assign a unique identifier
    instance.name = $"{modelName}_{Guid.NewGuid()}";

    // Send success response
    JObject response = new JObject
    {
        ["status"] = "success",
        ["message"] = $"Model '{modelName}' placed at ({position.x}, {position.y}, {position.z})."
    };
    Send(response.ToString());
}