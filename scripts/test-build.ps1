# test-build.ps1
# Run after build-app.bat to verify all artifacts were produced correctly.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\test-build.ps1

# Navigate to project root (one level above scripts/)
Set-Location (Join-Path $PSScriptRoot "..")

$ErrorCount = 0

function Pass($msg) { Write-Host "  ✅  $msg" -ForegroundColor Green }
function Fail($msg) { Write-Host "  ❌  $msg" -ForegroundColor Red; $script:ErrorCount++ }
function Info($msg) { Write-Host "       $msg" -ForegroundColor Gray }
function Section($title) { Write-Host "`n── $title $('─' * [Math]::Max(0, 48 - $title.Length))" -ForegroundColor Cyan }

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  InternIQ 2.7 Build Validation" -ForegroundColor Cyan
Write-Host "============================================================"

# ── Backend executable ────────────────────────────────────────────────────────
Section "Python Backend"

$backend = "backend\dist\interniq-backend.exe"
if (Test-Path $backend) {
    $size = [Math]::Round((Get-Item $backend).Length / 1MB, 1)
    Pass "interniq-backend.exe exists ($size MB)"
    if ($size -lt 5)  { Fail "  Suspiciously small — build may be incomplete" }
    if ($size -gt 200) { Fail "  Suspiciously large — check excluded packages" }
} else {
    Fail "backend\dist\interniq-backend.exe not found"
    Info "Run: pyinstaller backend\interniq_prod.spec --distpath backend\dist --workpath backend\build_tmp --noconfirm"
}

# ── Frontend build ────────────────────────────────────────────────────────────
Section "React Frontend Build"

$dist = "frontend\dist\index.html"
if (Test-Path $dist) {
    Pass "frontend\dist\index.html exists"
} else {
    Fail "frontend\dist\index.html not found — run: cd frontend && npm run build"
}

# ── Electron release ──────────────────────────────────────────────────────────
Section "Electron Release Artifacts"

$releaseDir = "frontend\release"
$found = @()
if (Test-Path $releaseDir) {
    Get-ChildItem "$releaseDir\*.exe" | ForEach-Object {
        $size = [Math]::Round($_.Length / 1MB, 1)
        Pass "$($_.Name) ($size MB)"
        $found += $_.FullName
    }
    Get-ChildItem "$releaseDir\*.zip", "$releaseDir\*.blockmap" | ForEach-Object {
        Info "  Also found: $($_.Name)"
    }
}
if ($found.Count -eq 0) {
    Fail "No .exe files found in frontend\release\"
    Info "Run: cd frontend && npm run electron:build:win"
}

# ── Distribution zip ──────────────────────────────────────────────────────────
Section "Distribution Package"

if (Test-Path "InternIQ-2.7.0.zip") {
    $size = [Math]::Round((Get-Item "InternIQ-2.7.0.zip").Length / 1MB, 1)
    Pass "InternIQ-2.7.0.zip exists ($size MB)"
} else {
    Info "InternIQ-2.7.0.zip not found (optional)"
}

# ── Quick backend smoke test ──────────────────────────────────────────────────
Section "Backend Smoke Test (optional — takes ~10s)"

$runTest = Read-Host "  Run backend smoke test? [y/N]"
if ($runTest -match '^[Yy]') {
    Write-Host "  Starting backend..." -ForegroundColor Gray
    $proc = Start-Process -FilePath "backend\dist\interniq-backend.exe" -PassThru -WindowStyle Hidden
    Start-Sleep 8

    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5 -UseBasicParsing
        if ($resp.StatusCode -eq 200) {
            Pass "Backend responded: /health → 200 OK"
        } else {
            Fail "Backend responded with unexpected status: $($resp.StatusCode)"
        }
    } catch {
        Fail "Backend did not respond at http://127.0.0.1:8000/health"
        Info "Error: $_"
    } finally {
        if (-not $proc.HasExited) { $proc.Kill() }
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host "`n============================================================" -ForegroundColor Cyan
if ($ErrorCount -eq 0) {
    Write-Host "  ALL CHECKS PASSED — ready to distribute!" -ForegroundColor Green
} else {
    Write-Host "  $ErrorCount CHECK(S) FAILED — fix errors above and rebuild." -ForegroundColor Red
}
Write-Host "============================================================`n" -ForegroundColor Cyan
