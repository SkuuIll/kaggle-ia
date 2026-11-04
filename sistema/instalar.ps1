param([switch]$CheckOnly,[switch]$SkipApps)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$localPrograms = Join-Path $env:LOCALAPPDATA 'Programs'
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

function Find-Python {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        $candidate = @(& $launcher.Source -3 -c 'import sys; assert sys.version_info >= (3,11); print(sys.executable)' 2>$null)
        if ($LASTEXITCODE -eq 0 -and $candidate) { return [string]$candidate[-1] }
    }
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python -and $python.Source -notlike '*WindowsApps*') {
        & $python.Source -c 'import sys; assert sys.version_info >= (3,11)' 2>$null
        if ($LASTEXITCODE -eq 0) { return $python.Source }
    }
    return $null
}

function Download-VerifiedAsset($repository,$tag,$assetName,$expectedHash) {
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$repository/releases/tags/$tag" -Headers @{ 'User-Agent'='KaggleIAInstaller' }
    $asset = @($release.assets | Where-Object { $_.name -eq $assetName })
    if ($asset.Count -ne 1) { throw "No se encontro el archivo oficial $assetName" }
    if ($asset[0].digest -ne ('sha256:' + $expectedHash)) { throw 'El hash publicado no coincide con la version aprobada.' }
    $cacheRoot = Join-Path $env:LOCALAPPDATA 'KaggleIASetup'
    New-Item -ItemType Directory -Force -Path $cacheRoot | Out-Null
    $target = Join-Path $cacheRoot $assetName
    if (-not (Test-Path -LiteralPath $target) -or (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
        Invoke-WebRequest -Uri $asset[0].browser_download_url -OutFile $target -UseBasicParsing
    }
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) { throw 'Descarga con SHA256 incorrecto. No se ejecutara.' }
    return $target
}

try {
    $pythonExe = Find-Python
    $ssh = Get-Command ssh.exe -ErrorAction SilentlyContinue
    $openCode = Join-Path $localPrograms 'OpenCode\opencode.exe'
    $paseo = Join-Path $localPrograms 'Paseo\Paseo.exe'
    if ($CheckOnly) {
        Write-Output ('Python disponible: ' + [bool]$pythonExe)
        Write-Output ('OpenSSH disponible: ' + [bool]$ssh)
        Write-Output ('Entorno .venv listo: ' + (Test-Path -LiteralPath $venvPython))
        Write-Output ('OpenCode instalado: ' + (Test-Path -LiteralPath $openCode))
        Write-Output ('Paseo instalado: ' + (Test-Path -LiteralPath $paseo))
        Write-Output 'Comprobacion sin cambios; no inicia GPUs.'
        exit 0
    }
    if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { throw 'Este instalador es para Windows x64.' }
    if (-not $pythonExe) {
        $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if (-not $winget) { throw 'Instala Python3.12 desde python.org y vuelve a ejecutar INSTALAR.bat.' }
        & $winget.Source install --exact --id Python.Python.3.12 --scope user --silent --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar Python.' }
        $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
        $pythonExe = Find-Python
        if (-not $pythonExe) {
            $pythonExe = Join-Path $localPrograms 'Python\Python312\python.exe'
            if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Abri una terminal nueva y ejecuta INSTALAR.bat otra vez.' }
        }
    }
    $httpsClient = Test-Path -LiteralPath (Join-Path $PSScriptRoot '.private/api-clients.json')
    if (-not $ssh -and -not $httpsClient) { throw 'Falta Cliente OpenSSH: agregalo desde Caracteristicas opcionales de Windows y vuelve a ejecutar el instalador.' }
    if (-not (Test-Path -LiteralPath $venvPython)) {
        & $pythonExe -m venv (Join-Path $PSScriptRoot '.venv')
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno de Python.' }
    }
    $requirements = Join-Path $PSScriptRoot 'requirements.lock.txt'
    if (-not (Test-Path -LiteralPath $requirements)) { $requirements = Join-Path $PSScriptRoot 'requirements.txt' }
    & $venvPython -m pip install --disable-pip-version-check -r $requirements
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
    if (-not $SkipApps) {
        if (-not (Test-Path -LiteralPath $openCode)) {
            $archive = Download-VerifiedAsset 'anomalyco/opencode' 'v1.19.5' 'opencode-windows-x64-baseline.zip' 'e4dac5cd38a182a24e7b3e18853f01d08cdb137e50b3bd1397c1a89e54d28c63'
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            $zip = [IO.Compression.ZipFile]::OpenRead($archive)
            try {
                $entry = @($zip.Entries | Where-Object { $_.Name -eq 'opencode.exe' })
                if ($entry.Count -ne 1) { throw 'El ZIP oficial no contiene un ejecutable unico.' }
                New-Item -ItemType Directory -Force -Path (Split-Path -Parent $openCode) | Out-Null
                [IO.Compression.ZipFileExtensions]::ExtractToFile($entry[0],$openCode,$true)
            } finally { $zip.Dispose() }
        }
        if (-not (Test-Path -LiteralPath $paseo)) {
            $setup = Download-VerifiedAsset 'getpaseo/paseo' 'v0.14.0' 'Paseo-Setup-0.14.0-x64.exe' 'd306794bcfc9341881f22f3900e076375d84e414718b36b752759d51eb49538f'
            $process = Start-Process -FilePath $setup -ArgumentList '/S' -WindowStyle Hidden -Wait -PassThru
            if ($process.ExitCode -notin @(0,3010)) { throw 'El instalador de Paseo no termino correctamente.' }
            if (-not (Test-Path -LiteralPath $paseo)) { throw 'No se encontro Paseo despues de instalarlo.' }
        }
    }
    if ($httpsClient) { Write-Output 'Instalacion preparada. Ejecuta CONFIGURAR_CLIENTES.bat y despues ABRIR_PASEO.bat.' }
    else { Write-Output 'Instalacion preparada. Inicia el panel o importa tu conexion privada.' }
    Write-Output 'No se inicio ninguna GPU.'
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
