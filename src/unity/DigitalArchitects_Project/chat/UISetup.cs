using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class UISetupHelper : MonoBehaviour
{
    public static GameObject CreateBasicUI()
    {
        // Create Canvas
        GameObject canvasObj = new GameObject("DigitalArchitectCanvas");
        Canvas canvas = canvasObj.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvasObj.AddComponent<CanvasScaler>();
        canvasObj.AddComponent<GraphicRaycaster>();

        // Create Chat Panel
        GameObject chatPanel = CreatePanel(canvasObj.transform, "ChatPanel");
        chatPanel.GetComponent<RectTransform>().anchoredPosition = new Vector2(0, 0);
        
        // Create Input Field
        GameObject inputField = CreateInputField(chatPanel.transform);
        
        // Create Message Container
        GameObject messageContainer = CreateScrollView(chatPanel.transform);
        
        // Create Debug Panel
        GameObject debugPanel = CreateDebugPanel(canvasObj.transform);

        return canvasObj;
    }

    private static GameObject CreatePanel(Transform parent, string name)
    {
        GameObject panel = new GameObject(name);
        panel.transform.SetParent(parent);
        
        RectTransform rect = panel.AddComponent<RectTransform>();
        rect.anchorMin = Vector2.zero;
        rect.anchorMax = Vector2.one;
        rect.sizeDelta = Vector2.zero;
        
        return panel;
    }

    // Additional helper methods for UI creation...
}