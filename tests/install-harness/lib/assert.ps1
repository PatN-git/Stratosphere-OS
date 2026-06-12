# Shared assertion + reporting helpers for the install-harness.
# Style follows src/skills/plan-html/test/agentic-eval.ps1: simple counters,
# colour-coded PASS/FAIL, exit 0/1 from Summary.

$script:Pass = 0
$script:Fail = 0
$script:Failures = @()

function Assert([string]$label, [bool]$cond) {
    if ($cond) {
        Write-Host "  PASS  $label" -ForegroundColor Green
        $script:Pass++
    } else {
        Write-Host "  FAIL  $label" -ForegroundColor Red
        $script:Fail++
        $script:Failures += $label
    }
}

function AssertEq([string]$label, $actual, $expected) {
    Assert "$label (got '$actual', expected '$expected')" ($actual -eq $expected)
}

function AssertPathExists([string]$label, [string]$path) {
    Assert "$label : $path" (Test-Path -LiteralPath $path)
}

function AssertFileCount([string]$label, [string]$dir, [string]$filter, [int]$expected) {
    $n = 0
    if (Test-Path -LiteralPath $dir) {
        $n = (Get-ChildItem -LiteralPath $dir -Filter $filter -File -ErrorAction SilentlyContinue | Measure-Object).Count
    }
    AssertEq "$label" $n $expected
}

function Section([string]$name) { Write-Host "`n== $name ==" -ForegroundColor Cyan }

function Summary() {
    Write-Host "`n----- install-harness L1: $script:Pass passed, $script:Fail failed -----"
    if ($script:Fail -gt 0) {
        Write-Host "Failures:" -ForegroundColor Red
        $script:Failures | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        exit 1
    }
    exit 0
}
