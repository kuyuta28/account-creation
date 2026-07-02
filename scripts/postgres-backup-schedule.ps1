<#
.SYNOPSIS
  Install/uninstall a Windows Scheduled Task that runs the daily Postgres backup.

.DESCRIPTION
  Creates a Scheduled Task "account-creation-pg-backup" that runs
  scripts/postgres-backup.ps1 daily at 03:07 (off the :00/:30 marks to avoid
  colliding with other scheduled jobs). Backups land in backups/postgres with
  retention handled by the backup script itself (default 14 days).

  The task runs whether or not you are logged in, but only when the machine is
  on. If the machine is off at the scheduled time, the task runs on next wake
  (StartWhenAvailable). It runs as the current user.

  Override defaults with env vars:
    BACKUP_TASK_TIME   "03:07"   (daily trigger time, HH:mm 24h)
    BACKUP_TASK_NAME   "account-creation-pg-backup"

.PARAMETER Uninstall
  Remove the scheduled task instead of creating it.

.EXAMPLE
  pwsh scripts/postgres-backup-schedule.ps1
  pwsh scripts/postgres-backup-schedule.ps1 -Uninstall
#>
[CmdletBinding()]
param(
  [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$TaskName = if ($env:BACKUP_TASK_NAME) { $env:BACKUP_TASK_NAME } else { "account-creation-pg-backup" }

if ($Uninstall) {
  if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[schedule] removed task: $TaskName"
  } else {
    Write-Host "[schedule] no task named $TaskName (nothing to do)"
  }
  return
}

$Time = if ($env:BACKUP_TASK_TIME) { $env:BACKUP_TASK_TIME } else { "03:07" }
$Script = Join-Path $Root "scripts\postgres-backup.ps1"
if (-not (Test-Path $Script)) { throw "backup script not found: $Script" }

# Idempotent: replace if it already exists.
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# pwsh if available, else powershell.exe (Windows PowerShell 5.1).
$Pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
$Shell = if ($Pwsh) { $Pwsh } else { "powershell.exe" }

$Action = New-ScheduledTaskAction `
  -Execute $Shell `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Script`""

$Trigger = New-ScheduledTaskTrigger -Daily -At $Time

$Settings = New-ScheduledTaskSettingsSet `
  -StartWhenAvailable `
  -DontStopOnIdleEnd `
  -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Run as the current interactive user. Local single-user dev box: the machine
# is normally logged-in, so Interactive (no stored password, no admin needed to
# register) is the simplest reliable choice. If you need it to run while logged
# out, re-register from an elevated shell and switch LogonType to S4U.
$Principal = New-ScheduledTaskPrincipal `
  -UserId "$env:USERDOMAIN\$env:USERNAME" `
  -LogonType Interactive `
  -RunLevel Limited

Register-ScheduledTask `
  -TaskName $TaskName `
  -Action $Action `
  -Trigger $Trigger `
  -Settings $Settings `
  -Principal $Principal `
  -Description "Daily account-creation Postgres backup. Uninstall: pwsh scripts/postgres-backup-schedule.ps1 -Uninstall" | Out-Null

Write-Host "[schedule] installed task: $TaskName (daily at $Time, working dir: $Root)"
Write-Host "[schedule] next run info: Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo"
Write-Host "[schedule] run now to test: Start-ScheduledTask -TaskName $TaskName"
