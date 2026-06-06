$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
$DistDir = Join-Path $ProjectRoot "dist\iOSRealRun-GUI"
$BuildDir = Join-Path $ProjectRoot "build\iOSRealRun-GUI"
$SpecDir = Join-Path $ProjectRoot "build"

if ($DistDir.StartsWith($ProjectRoot) -and (Test-Path $DistDir)) {
  Remove-Item $DistDir -Recurse -Force
}
New-Item -ItemType Directory -Path $DistDir -Force | Out-Null

Write-Host "Installing packaging dependencies..."
python -m pip install -r requirements.txt
python -m pip install pyinstaller

Write-Host "Building GUI executable..."
python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onefile `
  --name iOSRealRun-GUI `
  --distpath "$DistDir" `
  --workpath "$BuildDir" `
  --specpath "$SpecDir" `
  gui.py

$DistLibDir = Join-Path $DistDir "libimobiledevice"

Write-Host "Copying runtime resources..."
Copy-Item "config.yaml" $DistDir -Force
Copy-Item "*route.txt" $DistDir -Force
Copy-Item "DeveloperDiskImage" $DistDir -Recurse -Force
New-Item -ItemType Directory -Path $DistLibDir -Force | Out-Null
Copy-Item "libimobiledevice\win" $DistLibDir -Recurse -Force

Write-Host ""
Write-Host "Build complete:"
Write-Host "  $DistDir\iOSRealRun-GUI.exe"
