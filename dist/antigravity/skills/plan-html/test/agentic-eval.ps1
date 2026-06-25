# plan-html Agentic Evaluation Suite
# Covers: (1) Four-Scenario Gate logic, (2) Output artifact existence + header validation
Write-Host "`n=== plan-html Agentic Evaluation ===" -ForegroundColor Cyan

$root = Split-Path $PSScriptRoot -Parent
$outputDir = Join-Path $PSScriptRoot "output"
$pass = 0; $fail = 0

function Assert($label, $result, $expected) {
  if ($result -eq $expected) {
    Write-Host "  PASS  $label" -ForegroundColor Green
    $script:pass++
  } else {
    Write-Host "  FAIL  $label (got '$result', expected '$expected')" -ForegroundColor Red
    $script:fail++
  }
}

# ─── Part 1: Gate Logic ────────────────────────────────────────────────────
Write-Host "`n[1] Gate Logic" -ForegroundColor Yellow

function Gate($consumer, $spatial, $ratio) {
  if ($consumer -eq 'human' -and $spatial -and $ratio -lt 5.0) { return 'html' }
  return 'markdown'
}

Assert "Checklist (human, no spatial)"          (Gate 'human' $false 2.0) 'markdown'
Assert "Trade-off matrix (human, spatial, 3.5x)" (Gate 'human' $true  3.5) 'html'
Assert "Agent loop (agent, spatial)"             (Gate 'agent' $true  2.0) 'markdown'
Assert "Bloated HTML (human, spatial, 5.5x)"    (Gate 'human' $true  5.5) 'markdown'
Assert "Repo README (repo, no spatial)"          (Gate 'repo'  $false 1.5) 'markdown'

# ─── Part 2: New Scenarios ─────────────────────────────────────────────────
Write-Host "`n[2] Extended Scenarios" -ForegroundColor Yellow

Assert "KPI dashboard (human, spatial, 4.0x)"      (Gate 'human' $true  4.0) 'html'
Assert "Incident timeline (human, spatial, 3.8x)"   (Gate 'human' $true  3.8) 'html'
Assert "Decision record (human, spatial, 3.0x)"     (Gate 'human' $true  3.0) 'html'
Assert "Agent-to-agent context (agent, no spatial)" (Gate 'agent' $false 1.5) 'markdown'
Assert "Tech spec doc (repo, spatial, 2.0x)"        (Gate 'repo'  $true  2.0) 'markdown'

# ─── Part 3: Artifact Existence + Header Validation ────────────────────────
Write-Host "`n[3] E2E Artifact Validation" -ForegroundColor Yellow

$artifacts = @(
  @{ file = "db-options-matrix.html";  ratio = "3.1x"; template = "trade-off-matrix" },
  @{ file = "complex-plan-document.html"; ratio = "3.0x"; template = "plan-document" },
  @{ file = "triage-board.html"; ratio = "3.6x"; template = "board" }
)

foreach ($a in $artifacts) {
  $path = Join-Path $outputDir $a.file
  $exists = Test-Path $path
  Assert "Artifact exists: $($a.file)" $exists $true

  if ($exists) {
    $content = Get-Content $path -Raw
    $hasHeader  = $content -match '<!-- plan-html \|'
    $hasRatio   = $content -match [regex]::Escape($a.ratio)
    $hasPlanData= $content -match 'id="plan-data"'
    $hasExport  = $content -match 'exportMd\(\)'
    Assert "  Header comment present"   $hasHeader  $true
    Assert "  Correct ratio logged"     $hasRatio   $true
    Assert "  State script present"     $hasPlanData $true
    Assert "  Export MD button present" $hasExport  $true

    # Assert plan-data parses to a non-empty object
    $jsonStart = $content.IndexOf('id="plan-data" type="application/json">')
    if ($jsonStart -ge 0) {
      $jsonStart += 'id="plan-data" type="application/json">'.Length
    } else {
      $jsonStart = $content.IndexOf('id="plan-data">')
      if ($jsonStart -ge 0) {
        $jsonStart += 'id="plan-data">'.Length
      }
    }
    if ($jsonStart -ge 0) {
      $jsonEnd = $content.IndexOf('</script>', $jsonStart)
      if ($jsonEnd -ge 0) {
        $jsonStr = $content.Substring($jsonStart, $jsonEnd - $jsonStart).Trim()
        try {
          $parsed = ConvertFrom-Json $jsonStr
          $isNotEmpty = $null -ne $parsed -and ($parsed.psobject.properties.Count -gt 0 -or $parsed.Length -gt 0)
          Assert "  State script parses to non-empty object" $isNotEmpty $true
        } catch {
          Assert "  State script parses as JSON" $false $true
        }
      } else {
        Assert "  State script closing tag found" $false $true
      }
    } else {
      Assert "  State script id found" $false $true
    }
  }
}

# ─── Part 4: Template Index Coverage ──────────────────────────────────────
Write-Host "`n[4] Template Index Coverage" -ForegroundColor Yellow

$templateDir = Join-Path $root "assets\templates"
$expectedTemplates = @(
  "index.md","trade-off-matrix.html",
  "status-report.html","incident-timeline.html","decision-record.html","wireframe-compare.html",
  "plan-document.html","board.html"
)

foreach ($t in $expectedTemplates) {
  $exists = Test-Path (Join-Path $templateDir $t)
  Assert "Template exists: $t" $exists $true
}

# ─── Summary ──────────────────────────────────────────────────────────────
Write-Host "`n=== Results: $pass passed, $fail failed ===" -ForegroundColor $(if ($fail -eq 0) {'Green'} else {'Red'})
exit $(if ($fail -eq 0) {0} else {1})
