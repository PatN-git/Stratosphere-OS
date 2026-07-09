<#
  L1 - deterministic install/scaffold/sync E2E (no agent).
  Matrix: {Claude, Antigravity} x {local, global}, PowerShell installers.

  Isolation: each cell uses a throwaway project dir under $env:TEMP. --global
  cells also redirect HOME to a throwaway dir (real ~/.claude and ~/.gemini are
  never written). The current scaffold.py performs no system mutation (no
  git/pip), so no venv is required; a leak check at the end confirms the real
  homes are untouched.

  Run from anywhere:
    powershell -ExecutionPolicy Bypass -File tests/install-harness/run-L1.ps1
#>
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $here "lib\assert.ps1")
. (Join-Path $here "lib\isolation.ps1")

$repo = (Resolve-Path (Join-Path $here "..\..")).Path
Write-Host "Repo: $repo"

if (-not (Test-Path (Join-Path $repo "dist\claude-code")) -or -not (Test-Path (Join-Path $repo "dist\antigravity"))) {
    Write-Host "Building dist/ ..."
    python (Join-Path $repo "build\build.py") | Out-Null
}

$realBefore = Get-RealHomeSnapshot

function Assert-ScaffoldTree([string]$proj) {
    foreach ($f in @("AGENT.md","CLAUDE.md","GEMINI.md",".gitignore",".gitattributes","index.md")) {
        AssertPathExists "scaffold: $f" (Join-Path $proj $f)
    }
    AssertFileCount "scaffold: .memory/*.md == 9" (Join-Path $proj ".memory") "*.md" 9
    AssertFileCount "scaffold: .agents/rules/*.md == 3" (Join-Path $proj ".agents\rules") "*.md" 3
    AssertFileCount "scaffold: .agents/workflows/*.md == 17" (Join-Path $proj ".agents\workflows") "*.md" 17
    AssertPathExists "scaffold: validate_memory.py" (Join-Path $proj ".agents\scripts\validate_memory.py")
    AssertPathExists "scaffold: okf_view.py" (Join-Path $proj ".agents\scripts\okf_view.py")
    AssertPathExists "scaffold: okf_viewer/generator.py" (Join-Path $proj ".agents\scripts\okf_viewer\generator.py")
    AssertPathExists "scaffold: docs/discovery/.gitkeep" (Join-Path $proj "docs\discovery\.gitkeep")
    AssertPathExists "scaffold: docs/knowledge/index.md" (Join-Path $proj "docs\knowledge\index.md")
    $gi = Get-Content (Join-Path $proj ".gitignore") -Raw -ErrorAction SilentlyContinue
    Assert "scaffold: .gitignore contains *.work.md" ($gi -match '\*\.work\.md')
}

function Run-Cell([string]$tool, [string]$scope) {
    # $tool: "claude-code" | "antigravity"   $scope: "local" | "global"
    Section "$tool / $scope (ps1)"
    $proj = New-TempDir "sos-proj"
    $tmpHome = if ($scope -eq "global") { New-TempDir "sos-home" } else { $null }
    try {
        $installer = Join-Path $repo "scripts\install-$tool.ps1"

        # --- install (failure throws via the installer's ErrorActionPreference=Stop) ---
        if ($scope -eq "local") {
            Push-Location $proj
            & $installer --local | Write-Host
            Pop-Location
        } else {
            Invoke-PsInstallerGlobal $tmpHome $installer @('--global')
        }

        # --- resolve landing spot + assert install tree ---
        if ($tool -eq "claude-code") {
            $base = if ($scope -eq "local") { Join-Path $proj ".claude" } else { Join-Path $tmpHome ".claude" }
            $pluginRoot = Join-Path $base "plugins\stratosphere-os"
            AssertFileCount "install: .claude/commands/*.md == 19" (Join-Path $base "commands") "*.md" 19
            AssertPathExists "install: skills/micro-tdd" (Join-Path $base "skills\micro-tdd")
            AssertPathExists "install: skills/plan-html" (Join-Path $base "skills\plan-html")
        } else {
            $pluginRoot = if ($scope -eq "local") { Join-Path $proj ".agents\plugins\stratosphere-os" } else { Join-Path $tmpHome ".gemini\config\plugins\stratosphere-os" }
            AssertPathExists "install: plugin.json" (Join-Path $pluginRoot "plugin.json")
            AssertFileCount "install: workflows/*.md == 17" (Join-Path $pluginRoot "workflows") "*.md" 17
            Assert "install: no stratosphere-setup.md in workflows" (-not (Test-Path (Join-Path $pluginRoot "workflows\stratosphere-setup.md")))
        }
        AssertPathExists "install: bundled scaffold.py" (Join-Path $pluginRoot "scripts\scaffold.py")

        # --- scaffold (pure file creation in cwd) ---
        $scaffold = Join-Path $pluginRoot "scripts\scaffold.py"
        if ($scope -eq "local") {
            Push-Location $proj
            $out = & python $scaffold 2>&1 | Out-String
            Pop-Location
        } else {
            $out = Invoke-PyWithHome $tmpHome $proj @($scaffold)
        }
        Assert "scaffold reports applied" ($out -match 'StratosphereOS scaffold \(applied\)')
        Assert-ScaffoldTree $proj

        # --- sync (offline dry-run) ---
        $sync = Join-Path $pluginRoot "scripts\sync_skills.py"
        $syncArgs = @($sync, '--category', 'system', '--dry-run')
        if ($scope -eq "global") { $syncArgs += '--global' }
        if ($scope -eq "local") {
            Push-Location $proj
            $sout = & python @syncArgs 2>&1 | Out-String
            Pop-Location
        } else {
            $sout = Invoke-PyWithHome $tmpHome $proj $syncArgs
        }
        Assert "sync reports $scope scope" ($sout -match "\($scope scope\)")
        Assert "sync is dry-run (no download)" ($sout -match '\[DRY\]')
    }
    finally {
        Remove-Temp $proj
        if ($tmpHome) { Remove-Temp $tmpHome }
    }
}

foreach ($tool in @("claude-code","antigravity")) {
    foreach ($scope in @("local","global")) {
        Run-Cell $tool $scope
    }
}

Section "leak check"
$realAfter = Get-RealHomeSnapshot
foreach ($k in $realBefore.Keys) {
    AssertEq "real home untouched: $k" $realAfter[$k] $realBefore[$k]
}

Summary
