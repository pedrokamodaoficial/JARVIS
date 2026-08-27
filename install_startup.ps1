# install_startup.ps1
#
# Cria um atalho na pasta de Inicialização do Windows apontando para o
# Jarvis (jarvis_tray.py), rodado com pythonw.exe (sem janela de console).
# Depois de rodar este script uma vez, o Jarvis passa a iniciar sozinho
# toda vez que voce fizer login no Windows.
#
# Como usar (PowerShell, dentro da pasta do projeto):
#   powershell -ExecutionPolicy Bypass -File install_startup.ps1

$WshShell = New-Object -ComObject WScript.Shell
$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "Jarvis.lnk"

$projectDir = $PSScriptRoot
$pythonwPath = Join-Path $projectDir "venv\Scripts\pythonw.exe"
$scriptPath = Join-Path $projectDir "jarvis_tray.py"

if (-Not (Test-Path $pythonwPath)) {
    Write-Host "AVISO: nao encontrei $pythonwPath"
    Write-Host "Isso espera que voce tenha criado um ambiente virtual chamado 'venv' dentro desta pasta."
    Write-Host "Se voce nao usa venv, ou usa outro nome, edite a variavel `$pythonwPath` neste script"
    Write-Host "apontando para o pythonw.exe correto (geralmente ao lado do python.exe que voce usa)."
    exit 1
}

if (-Not (Test-Path $scriptPath)) {
    Write-Host "AVISO: nao encontrei $scriptPath"
    Write-Host "Confirme que este script esta na mesma pasta que o jarvis_tray.py."
    exit 1
}

$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $pythonwPath
$Shortcut.Arguments = "`"$scriptPath`""
$Shortcut.WorkingDirectory = $projectDir
$Shortcut.IconLocation = $pythonwPath
$Shortcut.Save()

Write-Host ""
Write-Host "Atalho criado em:"
Write-Host "  $shortcutPath"
Write-Host ""
Write-Host "O Jarvis vai iniciar automaticamente no proximo login do Windows."
Write-Host "Para iniciar AGORA sem reiniciar o Windows, de dois cliques no atalho acima"
Write-Host "ou rode: & `"$pythonwPath`" `"$scriptPath`""