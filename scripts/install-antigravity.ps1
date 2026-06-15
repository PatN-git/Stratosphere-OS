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
    $pluginDir = Join-Path $HOME ".gemini\config\plugins\stratosphere-os"
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

Write-Host "Successfully installed to $pluginDir. Restart Google Antigravity (or start a new agent session), then run /stratosphere-setup in your project."
