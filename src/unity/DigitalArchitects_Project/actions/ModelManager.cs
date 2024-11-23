using UnityEngine;
using System.Threading.Tasks;
using System.Collections.Generic;
using System;

public class ModelManager : MonoBehaviour
{
    [SerializeField] private Transform modelsContainer;
    [SerializeField] private Dictionary<string, GameObject> modelPrefabs;

    private Dictionary<string, GameObject> activeModels = new Dictionary<string, GameObject>();

    public async Task<GameObject> LoadAndPlaceModel(string modelName, Vector3 position, Quaternion rotation)
    {
        try
        {
            GameObject prefab = await LoadModelPrefab(modelName);
            if (prefab == null) return null;

            GameObject instance = Instantiate(prefab, position, rotation, modelsContainer);
            string instanceId = Guid.NewGuid().ToString();
            activeModels[instanceId] = instance;

            return instance;
        }
        catch (Exception e)
        {
            Debug.LogError($"Error loading/placing model {modelName}: {e.Message}");
            return null;
        }
    }

    private async Task<GameObject> LoadModelPrefab(string modelName)
    {
        // First check if it's in our preloaded prefabs
        if (modelPrefabs.TryGetValue(modelName, out GameObject prefab))
            return prefab;

        // Otherwise, try to load from Resources
        try
        {
            var loadedPrefab = Resources.Load<GameObject>($"Models/{modelName}");
            if (loadedPrefab != null)
            {
                modelPrefabs[modelName] = loadedPrefab;
                return loadedPrefab;
            }
            
            Debug.LogError($"Model {modelName} not found");
            return null;
        }
        catch (Exception e)
        {
            Debug.LogError($"Error loading model {modelName}: {e.Message}");
            return null;
        }
    }

    public void RemoveModel(string instanceId)
    {
        if (activeModels.TryGetValue(instanceId, out GameObject model))
        {
            Destroy(model);
            activeModels.Remove(instanceId);
        }
    }

    public void ClearAllModels()
    {
        foreach (var model in activeModels.Values)
        {
            if (model != null)
                Destroy(model);
        }
        activeModels.Clear();
    }
}