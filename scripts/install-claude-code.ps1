$ErrorActionPreference = "Stop"

# Resolve repo root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")

$buildDir = Join-Path $repoRoot "dist\claude-code"
if (-not (Test-Path $buildDir) -or -not (Get-ChildItem $buildDir -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1)) {
    Write-Error "dist/claude-code is missing or empty - run 'python build/build.py' first."
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

$resolvedTarget = if ($targetDir) { $targetDir } else { (Get-Location).Path }

if ($scope -eq "global") {
    $baseHome = if ($env:USERPROFILE) { $env:USERPROFILE } elseif ($env:HOME) { $env:HOME } else { $HOME }
    $claudeDir = Join-Path $baseHome ".claude"
    Write-Host "Installing globally under ~/.claude/..."
} else {
    $claudeDir = Join-Path $resolvedTarget ".claude"
    Write-Host "Installing locally under $claudeDir..."
}

$commandsDir = Join-Path $claudeDir "commands"
$skillsDir = Join-Path $claudeDir "skills"
$pluginsDir = Join-Path $claudeDir "plugins\stratosphere-os"

# Replace each shipped entry wholesale (drops stale files inside it, e.g. a
# template removed upstream) while preserving foreign entries in shared dirs.
function Copy-Overlay($src, $dest) {
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    foreach ($item in Get-ChildItem -Path $src -Force) {
        $target = Join-Path $dest $item.Name
        if (Test-Path $target) { Remove-Item -Path $target -Recurse -Force }
        Copy-Item -Path $item.FullName -Destination $target -Recurse -Force
    }
}

if (Test-Path (Join-Path $buildDir "commands")) { Copy-Overlay (Join-Path $buildDir "commands") $commandsDir }
if (Test-Path (Join-Path $buildDir "skills")) { Copy-Overlay (Join-Path $buildDir "skills") $skillsDir }

# Stage full plugin to plugins/stratosphere-os/ (skills/ merged per skill).
New-Item -ItemType Directory -Force -Path $pluginsDir | Out-Null
foreach ($item in Get-ChildItem -Path $buildDir -Force) {
    if ($item.PSIsContainer -and $item.Name -eq "skills") {
        Copy-Overlay $item.FullName (Join-Path $pluginsDir "skills")
    } else {
        $dest = Join-Path $pluginsDir $item.Name
        if (Test-Path $dest) { Remove-Item -Path $dest -Recurse -Force }
        Copy-Item -Path $item.FullName -Destination $dest -Recurse -Force
    }
}

# v4 retired two top-level bundle dirs. The overlay only replaces what the CURRENT
# bundle ships, so a dir we no longer ship is never touched and its stale v3 contents
# survive an upgrade. Both dirs are unambiguously framework-owned.
foreach ($retired in @("workflows", "commands")) {
    $retiredPath = Join-Path $pluginsDir $retired
    if (Test-Path $retiredPath) {
        Write-Host "Removing retired $retired/ from plugin dir (v3 leftovers)..."
        Remove-Item -Path $retiredPath -Recurse -Force
    }
}

Write-Host "Successfully installed to $claudeDir. Restart Claude Code for the commands to load."
