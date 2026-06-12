# Isolation primitives for the install-harness.
# Everything lives under $env:TEMP and is removed by Remove-Temp; the real
# ~/.claude and ~/.gemini are never written to.
#
# Note: the current scaffold.py only creates files under the project (cwd) and
# performs NO system mutation (no git init, no pip install), so no venv is
# needed. Global-scope cells still redirect HOME so installers and Python's
# Path.home() resolve to a throwaway directory.

function New-TempDir([string]$prefix) {
    $p = Join-Path $env:TEMP ("$prefix-" + [guid]::NewGuid().ToString('N').Substring(0,8))
    New-Item -ItemType Directory -Force -Path $p | Out-Null
    return $p
}

function Remove-Temp([string]$path) {
    if ($path -and (Test-Path -LiteralPath $path)) {
        Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Run a PowerShell installer with HOME redirected to $tmpHome. PowerShell's
# automatic $HOME is computed from HOMEDRIVE+HOMEPATH at process startup, so we
# set those (and USERPROFILE) in THIS process, then launch a child PowerShell
# that inherits them and computes the right $HOME. Env is restored afterwards.
function Invoke-PsInstallerGlobal([string]$tmpHome, [string]$scriptPath, [string[]]$scriptArgs) {
    $o = @{ HD = $env:HOMEDRIVE; HP = $env:HOMEPATH; UP = $env:USERPROFILE }
    try {
        $env:HOMEDRIVE   = $tmpHome.Substring(0,2)
        $env:HOMEPATH    = $tmpHome.Substring(2)
        $env:USERPROFILE = $tmpHome
        $argline = ($scriptArgs -join ' ')
        & powershell -NoProfile -ExecutionPolicy Bypass -Command "& '$scriptPath' $argline" | Write-Host
    } finally {
        $env:HOMEDRIVE = $o.HD; $env:HOMEPATH = $o.HP; $env:USERPROFILE = $o.UP
    }
}

# Run a Python script with USERPROFILE redirected (Path.home() uses USERPROFILE
# on Windows) so global scope detection / global skill paths resolve under the
# temp home. Returns combined output as a string.
function Invoke-PyWithHome([string]$tmpHome, [string]$workDir, [string[]]$pyArgs) {
    $old = $env:USERPROFILE
    try {
        $env:USERPROFILE = $tmpHome
        Push-Location $workDir
        $out = & python @pyArgs 2>&1 | Out-String
        Pop-Location
        return $out
    } finally {
        $env:USERPROFILE = $old
    }
}

# Snapshot the real homes' last-write time so cells can assert no leakage.
function Get-RealHomeSnapshot() {
    $snap = @{}
    foreach ($p in @("$HOME\.claude", "$HOME\.gemini\config\plugins")) {
        if (Test-Path -LiteralPath $p) { $snap[$p] = (Get-Item -LiteralPath $p).LastWriteTimeUtc.Ticks }
        else { $snap[$p] = $null }
    }
    return $snap
}
