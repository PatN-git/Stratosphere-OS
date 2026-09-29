<#
  L1 - deterministic install/scaffold/sync E2E for the canonical dist/skills bundle (no agent).
  Matrix: {.claude/skills, .agents/skills} x {local, global}, Track B direct copy
  (Copy-Item). There is no per-host installer: a skills installer only places skill
  folders, and stratosphere-setup carries its own scaffolder payload.

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

if (-not (Test-Path (Join-Path $repo "dist\skills"))) {
    Write-Host "Building dist/ ..."
    python (Join-Path $repo "build\build.py") | Out-Null
}

$realBefore = Get-RealHomeSnapshot

function Assert-ScaffoldTree([string]$proj) {
    foreach ($f in @("AGENTS.md","CLAUDE.md","GEMINI.md",".gitignore",".gitattributes","index.md")) {
        AssertPathExists "scaffold: $f" (Join-Path $proj $f)
    }
    AssertFileCount "scaffold: .memory/*.md == 9" (Join-Path $proj ".memory") "*.md" 9
    AssertFileCount "scaffold: .agents/rules/*.md == 3" (Join-Path $proj ".agents\rules") "*.md" 3
    Assert "scaffold: .agents/skills 26 SKILL.md" ((Get-ChildItem -Path (Join-Path $proj ".agents\skills") -Filter "SKILL.md" -Recurse -ErrorAction SilentlyContinue).Count -eq 26)
    Assert "scaffold: no legacy .agents/workflows" (-not (Test-Path (Join-Path $proj ".agents\workflows")))
    Assert "scaffold: copilot skills 26" ((Get-ChildItem -Path (Join-Path $proj ".github\copilot\skills") -Filter "SKILL.md" -Recurse -ErrorAction SilentlyContinue).Count -eq 26)
    Assert "scaffold: setup payload not copied into copilot skill" (-not (Test-Path (Join-Path $proj ".github\copilot\skills\stratosphere-setup\scripts")))
    AssertPathExists "scaffold: validate_memory.py" (Join-Path $proj ".agents\scripts\validate_memory.py")
    AssertPathExists "scaffold: okf_view.py" (Join-Path $proj ".agents\scripts\okf_view.py")
    AssertPathExists "scaffold: okf_viewer/generator.py" (Join-Path $proj ".agents\scripts\okf_viewer\generator.py")
    AssertPathExists "scaffold: docs/discovery/.gitkeep" (Join-Path $proj "docs\discovery\.gitkeep")
    AssertPathExists "scaffold: docs/knowledge/index.md" (Join-Path $proj "docs\knowledge\index.md")
    AssertPathExists "scaffold: docs/nightly/index.md" (Join-Path $proj "docs\nightly\index.md")
    $gi = Get-Content (Join-Path $proj ".gitignore") -Raw -ErrorAction SilentlyContinue
    Assert "scaffold: .gitignore contains *.work.md" ($gi -match '\*\.work\.md')
}

function Run-Cell([string]$hostDir, [string]$scope) {
    # $hostDir: ".claude" | ".agents"   $scope: "local" | "global"
    Section "$hostDir / $scope (ps1)"
    $proj = New-TempDir "sos-proj"
    $tmpHome = if ($scope -eq "global") { New-TempDir "sos-home" } else { $null }
    try {
        # --- Track B: plain copy of the canonical bundle, exactly as documented ---
        $root = if ($scope -eq "local") { $proj } else { $tmpHome }
        $base = Join-Path $root "$hostDir\skills"
        New-Item -ItemType Directory -Force -Path $base | Out-Null
        Copy-Item -Recurse -Force (Join-Path $repo "dist\skills\*") $base
        $bundle = Join-Path $base "stratosphere-setup"

        # --- assert bundle tree ---
        Assert "install: 26 skills" ((Get-ChildItem -Path $base -Directory | Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") }).Count -eq 26)
        Assert "install: 22 HITL sidecars" ((Get-ChildItem -Path $base -Directory | Where-Object { Test-Path (Join-Path $_.FullName "agents\openai.yaml") }).Count -eq 22)
        AssertPathExists "install: skills/micro-tdd" (Join-Path $base "micro-tdd\SKILL.md")
        Assert "install: no legacy commands/workflows dir" (-not ((Test-Path (Join-Path $base "commands")) -or (Test-Path (Join-Path $base "workflows"))))
        AssertPathExists "install: setup carries scaffold.py" (Join-Path $bundle "scripts\scaffold.py")
        AssertPathExists "install: setup carries versions.json" (Join-Path $bundle "versions.json")
        AssertPathExists "install: setup carries templates" (Join-Path $bundle "assets\templates\memory")

        # --- scaffold (pure file creation in cwd) ---
        $scaffold = Join-Path $bundle "scripts\scaffold.py"
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
        $sync = Join-Path $bundle "scripts\sync_skills.py"
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

foreach ($hostDir in @(".claude",".agents")) {
    foreach ($scope in @("local","global")) {
        Run-Cell $hostDir $scope
    }
}

Section "leak check"
$realAfter = Get-RealHomeSnapshot
foreach ($k in $realBefore.Keys) {
    AssertEq "real home untouched: $k" $realAfter[$k] $realBefore[$k]
}

Summary
