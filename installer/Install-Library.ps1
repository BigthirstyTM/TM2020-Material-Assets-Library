[CmdletBinding()]
param(
    [ValidateSet('materials-only', 'complete')][string]$Edition = 'materials-only',
    [string]$Version = '1.0.0',
    [string]$Repository = 'BigthirstyTM/TM2020-Material-Assets-Library',
    [string]$Destination,
    [string]$Blender,
    [string]$PackageDirectory,
    [switch]$SkipConfiguration
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
if (-not $Destination) {
    $Destination = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) "TM2020 Material Assets Library\$Edition\$Version"
}
$Destination = [IO.Path]::GetFullPath($Destination)
$cache = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) "TM2020 Material Assets Library\Downloads\$Version-$Edition"
if ($PackageDirectory) { $cache = (Resolve-Path -LiteralPath $PackageDirectory).Path }
else { New-Item -ItemType Directory -Path $cache -Force | Out-Null }
$baseUrl = "https://github.com/$Repository/releases/download/v$Version-$Edition"
$manifestPath = Join-Path $cache 'release.json'
Write-Host "Downloading $Edition $Version..."
if (-not $PackageDirectory) { Invoke-WebRequest -UseBasicParsing "$baseUrl/release.json" -OutFile $manifestPath }
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.edition -ne $Edition -or $manifest.version -ne $Version) { throw 'Release edition/version mismatch.' }
if (Test-Path -LiteralPath $Destination) { throw "Destination already exists. Choose another -Destination: $Destination" }
foreach ($asset in $manifest.archives) {
    if ($asset.name -notmatch '^[A-Za-z0-9._-]+\.zip$') { throw 'Invalid archive name.' }
    $archivePath = Join-Path $cache $asset.name
    if ((Test-Path -LiteralPath $archivePath) -and ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash -eq $asset.sha256)) {
        Write-Host "Using verified cached download: $($asset.name)"
    } else {
        if ($PackageDirectory) { throw "Missing or invalid local package: $($asset.name)" }
        Write-Host "Downloading $($asset.name) ($([math]::Round($asset.bytes / 1MB)) MB)..."
        Invoke-WebRequest -UseBasicParsing "$baseUrl/$($asset.name)" -OutFile $archivePath
    }
    if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash -ne $asset.sha256) { throw "Download checksum mismatch: $($asset.name)" }
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$stage = $Destination + '.installing-' + [Guid]::NewGuid().ToString('N')
New-Item -ItemType Directory -Path $stage -Force | Out-Null
$stagePrefix = $stage.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
$extracted = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($asset in $manifest.archives) {
    Write-Host "Extracting $($asset.name)..."
    $zip = [IO.Compression.ZipFile]::OpenRead((Join-Path $cache $asset.name))
    try {
        foreach ($entry in $zip.Entries) {
            if (-not $entry.Name) { continue }
            $target = [IO.Path]::GetFullPath((Join-Path $stage $entry.FullName))
            if (-not $target.StartsWith($stagePrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Archive path escapes the installation folder.' }
            if (-not $extracted.Add($entry.FullName.Replace('\', '/'))) { throw 'Duplicate archive entry.' }
            New-Item -ItemType Directory -Force -Path ([IO.Path]::GetDirectoryName($target)) | Out-Null
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $target, $false)
        }
    } finally { $zip.Dispose() }
}
Write-Host 'Checking installed files...'
$expectedFiles = @($manifest.files.PSObject.Properties)
if ($extracted.Count -ne $expectedFiles.Count) { throw 'Unexpected archive file count.' }
foreach ($file in $expectedFiles) {
    $target = [IO.Path]::GetFullPath((Join-Path $stage $file.Name))
    if (-not $target.StartsWith($stagePrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid manifest path.' }
    if (-not $extracted.Contains($file.Name)) { throw "Missing file: $($file.Name)" }
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $file.Value) { throw "Installed checksum mismatch: $($file.Name)" }
}
Move-Item -LiteralPath $stage -Destination $Destination
Write-Host "Installed to: $Destination"
if (-not $SkipConfiguration) {
    if (-not $Blender) {
        $found = Get-ChildItem -Path "$env:ProgramFiles\Blender Foundation\Blender *\blender.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
        if ($found) { $Blender = $found.FullName }
    }
    if ($Blender -and (Test-Path -LiteralPath $Blender)) {
        Write-Host 'Registering the library in Blender. Keep Blender closed until this finishes.'
        & $Blender --background --factory-startup --python-exit-code 1 --python (Join-Path $Destination 'configure_blender.py') -- --library $Destination
        if ($LASTEXITCODE -ne 0) { throw "Files installed, but Blender setup failed. Follow docs/INSTALLATION.md in $Destination" }
    } else {
        Write-Host "Blender was not found. Add this folder under Preferences > File Paths > Asset Libraries: $Destination"
        Write-Host "Set Blendermania Settings > Material Lib to: $(Join-Path $Destination 'MaterialLib.txt')"
    }
}
Write-Host 'Done. Open Blender and select TM2020 Material Assets Library in the Asset Browser.'
Write-Host "Offline catalogue: $(Join-Path $Destination 'Catalogue\index.html')"
