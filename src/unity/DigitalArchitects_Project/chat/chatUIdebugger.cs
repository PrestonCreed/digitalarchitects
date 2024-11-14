using UnityEngine;
using UnityEditor;
using System.Collections.Generic;

namespace DigitalArchitect.Debug
{
    #if UNITY_EDITOR
    public class ArchitectDebugWindow : EditorWindow
    {
        private Vector2 scrollPosition;
        private bool showProjectContext = true;
        private bool showCommunicationLogs = true;
        private bool showTaskProgress = true;

        [MenuItem("Digital Architect/Debug Window")]
        public static void ShowWindow()
        {
            GetWindow<ArchitectDebugWindow>("Architect Debug");
        }

        private void OnGUI()
        {
            scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);

            if (Application.isPlaying)
            {
                var architect = FindObjectOfType<DigitalArchitectManager>();
                if (architect != null)
                {
                    DrawDebugInfo(architect);
                }
                else
                {
                    EditorGUILayout.HelpBox("No Digital Architect found in scene.", MessageType.Warning);
                }
            }
            else
            {
                EditorGUILayout.HelpBox("Enter Play Mode to see debug information.", MessageType.Info);
            }

            EditorGUILayout.EndScrollView();
        }

        private void DrawDebugInfo(DigitalArchitectManager architect)
        {
            // Project Context
            showProjectContext = EditorGUILayout.Foldout(showProjectContext, "Project Context");
            if (showProjectContext)
            {
                EditorGUI.indentLevel++;
                // Draw project context info
                EditorGUI.indentLevel--;
            }

            // Communication Logs
            showCommunicationLogs = EditorGUILayout.Foldout(showCommunicationLogs, "Communication Logs");
            if (showCommunicationLogs)
            {
                EditorGUI.indentLevel++;
                // Draw communication logs
                EditorGUI.indentLevel--;
            }

            // Task Progress
            showTaskProgress = EditorGUILayout.Foldout(showTaskProgress, "Task Progress");
            if (showTaskProgress)
            {
                EditorGUI.indentLevel++;
                // Draw task progress
                EditorGUI.indentLevel--;
            }
        }
    }
    #endif
}