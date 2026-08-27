# uninstall_startup.ps1
#
# Remove o atalho de inicializacao automatica criado pelo install_startup.ps1.
# Depois de rodar este script, o Jarvis deixa de iniciar sozinho com o Windows
# (mas voce ainda pode roda-lo manualmente quando quiser).
#
# Como usar (PowerShell):
#   powershell -ExecutionPolicy Bypass -File uninstall_startup.ps1

$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "Jarvis.lnk"

if (Test-Path $shortcutPath) {
    Remove-Item $shortcutPath
    Write-Host "Atalho removido: $shortcutPath"
    Write-Host "O Jarvis nao vai mais iniciar automaticamente com o Windows."
} else {
    Write-Host "Nenhum atalho de inicializacao encontrado (nada para remover)."
}