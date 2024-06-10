@echo off
@echo This script will disable the "Recall" feature in Windows 11.
@echo If you want to continue, press any key, or close the window to exit.
@pause > nul

:: Check for admin rights
>nul 2>&1 "%userprofile%\temp.%username%.administratoraccess" || (
    @echo You need to run this script with administrative privileges.
    exit /b
)

:: Disable the "Recall" feature for the current user
reg add "HKEY_CURRENT_USER\Software\Policies\Microsoft\Windows\WindowsAI" /v "DisableAIDataAnalysis" /t REG_DWORD /d 1 /f

:: Disable the "Recall" feature for all users
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\WindowsAI" /v "DisableAIDataAnalysis" /t REG_DWORD /d 1 /f

@echo The "Recall" feature has been disabled. You need to restart your computer for the changes to take effect.
@pause
