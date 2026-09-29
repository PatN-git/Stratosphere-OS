# Antigravity fallback bridge (BT-120): skills.sh installs globally to ~/.gemini/antigravity/skills/,
# but Antigravity discovers skills under ~/.gemini/config/ (vercel-labs/skills#633). Until that is
# fixed upstream, physically copy dist/skills/* into ~/.gemini/config/skills/ (no symlinks).
#
#   powershell -File scripts\install-antigravity-bridge.ps1 [--target <skills-dir>]
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path (Join-Path $scriptDir "..") "dist\skills"
$baseHome = if ($env:USERPROFILE) { $env:USERPROFILE } elseif ($env:HOME) { $env:HOME } else { $HOME }
$target = Join-Path $baseHome ".gemini\config\skills"

for ($i = 0; $i -lt $args.Count; $i++) {
    if ($args[$i] -eq "--target") {
        if (($i + 1) -ge $args.Count) {
            [Console]::Error.WriteLine("Error: --target requires a <skills-dir> value.")
            exit 1
        }
        $target = $args[$i + 1]; $i++
    } elseif ($args[$i] -like "--target=?*") {
        $target = $args[$i].Substring("--target=".Length)
    } else {
        [Console]::Error.WriteLine("Error: unrecognised argument '$($args[$i])'. Usage: install-antigravity-bridge.ps1 [--target <skills-dir>]")
        exit 1
    }
}

if (-not (Test-Path $src) -or -not (Get-ChildItem $src -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1)) {
    [Console]::Error.WriteLine("Error: dist/skills is missing or empty. Please run 'python build/build.py' first.")
    exit 1
}

# Replace each shipped skill (drops stale files inside it); leave foreign skills untouched.
New-Item -ItemType Directory -Force -Path $target | Out-Null
$count = 0
foreach ($skill in Get-ChildItem -Directory -Path $src) {
    $dest = Join-Path $target $skill.Name
    if (Test-Path $dest) { Remove-Item -Path $dest -Recurse -Force }
    Copy-Item -Recurse -Force -Path $skill.FullName -Destination $dest
    $count++
}

Write-Host "Copied $count skills to $target. Restart Google Antigravity (or start a new agent session), then run /stratosphere-setup in your project."
