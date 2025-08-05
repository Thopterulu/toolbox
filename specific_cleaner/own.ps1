# À exécuter en tant qu'administrateur
$currentPath = Get-Location
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

Write-Host "🛠️ Prise de possession de : $currentPath"
takeown /F "$currentPath" /R

Write-Host "🔐 Attribution des droits à : $currentUser"
icacls "$currentPath" /grant "${currentUser}:(F)" /T /C

Write-Host "`n✅ Terminé. Vous avez maintenant l'accès complet à : $currentPath"
