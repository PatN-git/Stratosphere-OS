$ErrorActionPreference = "Stop"

# Resolve repo root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")

$buildDir = Join-Path $repoRoot "dist\antigravity"
if (-not (Test-Path $buildDir) -or -not (Get-ChildItem $buildDir -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1)) {
    Write-Error "Error: dist/antigravity is missing or empty. Please run 'python build/build.py' first."
    exit 1
}

$scope = $null
$targetDir = $null
$nextIsTarget = $false
# Check command line flags
foreach ($arg in $args) {
    if ($nextIsTarget) { $targetDir = $arg; $nextIsTarget = $false }
    elseif ($arg -eq "--global") { $scope = "global" }
    elseif ($arg -eq "--local") { $scope = "local" }
    elseif ($arg -eq "--target") { $nextIsTarget = $true }
}

# Prompt if not specified
if ($null -eq $scope) {
    if ([Environment]::UserInteractive) {
        $choice = Read-Host "Install StratosphereOS globally or locally for the current project? [global/local] (default: global)"
        if ($choice -eq "local") {
            $scope = "local"
        } else {
            $scope = "global"
        }
    } else {
        $scope = "global"
    }
}

if ($scope -eq "global") {
    # Confirmed against installed Antigravity plugins (android-cli, chrome-devtools, ...).
    $baseHome = if ($env:USERPROFILE) { $env:USERPROFILE } elseif ($env:HOME) { $env:HOME } else { $HOME }
    $pluginDir = Join-Path $baseHome ".gemini\config\plugins\stratosphere-os"
    Write-Host "Installing globally under ~/.gemini/config/plugins/stratosphere-os/..."
} else {
    $resolvedTarget = if ($targetDir) { $targetDir } else { (Get-Location).Path }
    $pluginDir = Join-Path $resolvedTarget ".agents\plugins\stratosphere-os"
    Write-Host "Installing locally under $pluginDir..."
}

# Overlay the bundle: replace every item we ship (dropping stale orphans such as
# renamed workflow files within those folders), but PRESERVE foreign entries.
# In particular, external skills fetched into skills/ by `sync_skills.py --global`
# on Antigravity must survive a plugin update, so skills/ is merged per-skill.
New-Item -ItemType Directory -Force -Path $pluginDir | Out-Null
foreach ($item in Get-ChildItem -Force -Path $buildDir) {
    $dest = Join-Path $pluginDir $item.Name
    if ($item.PSIsContainer -and $item.Name -eq "skills") {
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        foreach ($skill in Get-ChildItem -Force -Path $item.FullName) {
            $skillDest = Join-Path $dest $skill.Name
            if (Test-Path $skillDest) { Remove-Item -Path $skillDest -Recurse -Force }
            Copy-Item -Path $skill.FullName -Destination $skillDest -Recurse -Force
        }
    } else {
        if (Test-Path $dest) { Remove-Item -Path $dest -Recurse -Force }
        Copy-Item -Path $item.FullName -Destination $dest -Recurse -Force
    }
}

# Record provenance so /stratosphere-update can self-update this copy-based install.
# The plugin dir is not a git checkout; without a recorded source, the update workflow
# cannot locate what to pull/fetch and falls back to manual instructions.
$sourceRepo = $null
try { $sourceRepo = (& git -C $repoRoot remote get-url origin 2>$null) } catch {}
if (-not $sourceRepo) { $sourceRepo = "https://github.com/PatN-git/Stratosphere-OS" }
$pluginVersion = ""
$versionsFile = Join-Path $buildDir "versions.json"
if (Test-Path $versionsFile) {
    try { $pluginVersion = (Get-Content $versionsFile -Raw | ConvertFrom-Json).plugin_version } catch {}
}
$provenance = [ordered]@{
    source_repo       = "$sourceRepo".Trim()
    source_clone      = "$repoRoot"
    plugin_dir        = "$pluginDir"
    scope             = $scope
    installer         = "install-antigravity.ps1"
    installed_version = $pluginVersion
}
# BOM-less UTF-8 so any strict JSON parser can read it (Out-File -Encoding utf8 emits a BOM on PS 5.1).
[System.IO.File]::WriteAllText((Join-Path $pluginDir ".install-source.json"), ($provenance | ConvertTo-Json), (New-Object System.Text.UTF8Encoding($false)))

Write-Host "Successfully installed to $pluginDir. Restart Google Antigravity (or start a new agent session), then run /stratosphere-setup in your project."
