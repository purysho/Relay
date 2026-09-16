$ErrorActionPreference = "Stop"
py -m pip install --upgrade pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name Relay relay_desktop.pyw
Write-Host "Built dist\Relay.exe"
