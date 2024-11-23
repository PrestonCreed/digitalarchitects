using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class UIPrefabManager : MonoBehaviour
{
    [Header("Chat UI")]
    [SerializeField] private GameObject chatPanel;
    [SerializeField] private TMP_InputField inputField;
    [SerializeField] private Button sendButton;
    [SerializeField] private ScrollRect chatScrollRect;
    [SerializeField] private RectTransform messageContainer;

    [Header("Message Prefabs")]
    [SerializeField] private GameObject userMessagePrefab;
    [SerializeField] private GameObject agentMessagePrefab;
    [SerializeField] private GameObject systemMessagePrefab;

    [Header("Debug Panel")]
    [SerializeField] private GameObject debugPanel;
    [SerializeField] private TextMeshProUGUI connectionStatus;
    [SerializeField] private TextMeshProUGUI lastMessageReceived;
    [SerializeField] private TextMeshProUGUI environmentStatus;

    [Header("Test Controls")]
    [SerializeField] private Button testConnectionButton;
    [SerializeField] private Button testActionButton;
    [SerializeField] private Toggle mockResponseToggle;

    private DigitalArchitectCore core;

    private void Awake()
    {
        core = FindObjectOfType<DigitalArchitectCore>();
        SetupUI();
    }

    private void SetupUI()
    {
        testConnectionButton?.onClick.AddListener(() => core.TestWebSocketConnection());
        testActionButton?.onClick.AddListener(() => core.TestEnvironmentAction());
        
        if (mockResponseToggle != null)
        {
            mockResponseToggle.onValueChanged.AddListener(value => 
            {
                // Update mock mode
                UpdateDebugStatus("Mock Mode: " + value);
            });
        }
    }

    public void UpdateDebugStatus(string status)
    {
        if (connectionStatus != null)
            connectionStatus.text = status;
    }

    public void UpdateLastMessage(string message)
    {
        if (lastMessageReceived != null)
            lastMessageReceived.text = message;
    }

    public void UpdateEnvironmentStatus(string status)
    {
        if (environmentStatus != null)
            environmentStatus.text = status;
    }

    // Add test methods for each component
}