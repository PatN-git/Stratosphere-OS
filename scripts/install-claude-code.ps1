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
    $claudeDir = Join-Path $HOME ".claude"
    Write-Host "Installing globally under ~/.claude/..."
} else {
    $claudeDir = Join-Path $resolvedTarget ".claude"
    Write-Host "Installing locally under $claudeDir..."
}

$commandsDir = Join-Path $claudeDir "commands"
$skillsDir = Join-Path $claudeDir "skills"
$pluginsDir = Join-Path $claudeDir "plugins\stratosphere-os"

# Create directories
New-Item -ItemType Directory -Force -Path $commandsDir | Out-Null
New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
New-Item -ItemType Directory -Force -Path $pluginsDir | Out-Null

# Copy commands
if (Test-Path (Join-Path $buildDir "commands")) {
    Copy-Item -Path (Join-Path $buildDir "commands\*") -Destination $commandsDir -Recurse -Force
}

# Copy skills
if (Test-Path (Join-Path $buildDir "skills")) {
    Copy-Item -Path (Join-Path $buildDir "skills\*") -Destination $skillsDir -Recurse -Force
}

# Stage full plugin to plugins/stratosphere-os/
Copy-Item -Path (Join-Path $buildDir "\*") -Destination $pluginsDir -Recurse -Force

Write-Host "Successfully installed to $claudeDir. Restart Claude Code for the commands to load."
