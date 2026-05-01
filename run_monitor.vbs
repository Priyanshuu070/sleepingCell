' run_monitor.vbs
' Runs monitor.py silently in the background with no terminal window.
' Double-click this file to start the monitor.
' To stop it: open Task Manager -> find pythonw.exe -> End Task
'             OR run in PowerShell: taskkill /F /IM pythonw.exe

Dim objShell
Dim strScriptDir
Dim strCommand

' Get the folder where this .vbs file lives
strScriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Build the command: pythonw runs Python with no console window
strCommand = "pythonw """ & strScriptDir & "\monitor.py"""

' Run it — the 0 means no window, False means don't wait for it to finish
Set objShell = CreateObject("WScript.Shell")
objShell.Run strCommand, 0, False

Set objShell = Nothing