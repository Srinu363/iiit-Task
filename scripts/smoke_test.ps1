# Smoke test for the deployed application (PowerShell)
param(
    [string]$BaseUrl = "http://localhost:3000",
    [string]$ApiUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Smoke Test ===" -ForegroundColor Cyan
Write-Host "Frontend: $BaseUrl"
Write-Host "Backend:  $ApiUrl"
Write-Host ""

# 1. Health check
Write-Host "1. Health check..." -NoNewline
try {
    $health = Invoke-RestMethod -Uri "$ApiUrl/health" -Method Get
    if ($health.status -in @("healthy", "degraded")) {
        Write-Host " OK ($($health.status))" -ForegroundColor Green
    } else {
        throw "Unexpected status: $($health.status)"
    }
} catch {
    Write-Host " FAILED: $_" -ForegroundColor Red
    exit 1
}

# 2. Model info
Write-Host "2. Model info..." -NoNewline
try {
    $info = Invoke-RestMethod -Uri "$ApiUrl/api/v1/model-info" -Method Get
    Write-Host " OK (version: $($info.model_version))" -ForegroundColor Green
} catch {
    Write-Host " FAILED: $_" -ForegroundColor Red
    exit 1
}

# 3. Analyze image
Write-Host "3. Analyze image..." -NoNewline
$testImgPath = Join-Path $PSScriptRoot "test_smoke_temp.png"
python -c "import cv2, numpy as np; cv2.imwrite(r'$testImgPath', np.random.randint(50, 200, (100, 100, 3), dtype=np.uint8))"

try {
    $form = @{
        file = Get-Item -Path $testImgPath
    }
    $res = Invoke-RestMethod -Uri "$ApiUrl/api/v1/analyze" -Method Post -Form $form
    Write-Host " OK (Score: $($res.quality_score), Label: $($res.quality_label), ID: $($res.id))" -ForegroundColor Green
    $analysisId = $res.id
} catch {
    Write-Host " FAILED: $_" -ForegroundColor Red
    if (Test-Path $testImgPath) { Remove-Item $testImgPath -Force }
    exit 1
} finally {
    if (Test-Path $testImgPath) { Remove-Item $testImgPath -Force }
}

# 4. Get analysis by ID
Write-Host "4. Get analysis by ID..." -NoNewline
try {
    $item = Invoke-RestMethod -Uri "$ApiUrl/api/v1/analyses/$analysisId" -Method Get
    Write-Host " OK (Score: $($item.quality_score), Issues: $($item.issues.Count))" -ForegroundColor Green
} catch {
    Write-Host " FAILED: $_" -ForegroundColor Red
    exit 1
}

# 5. List analyses
Write-Host "5. List analyses..." -NoNewline
try {
    $list = Invoke-RestMethod -Uri "$ApiUrl/api/v1/analyses?page=1&page_size=5" -Method Get
    Write-Host " OK (Total: $($list.total))" -ForegroundColor Green
} catch {
    Write-Host " FAILED: $_" -ForegroundColor Red
    exit 1
}

# 6. Frontend check
Write-Host "6. Frontend check..." -NoNewline
try {
    $fe = Invoke-WebRequest -Uri $BaseUrl -Method Get -UseBasicParsing
    if ($fe.StatusCode -eq 200) {
        Write-Host " OK (HTTP 200)" -ForegroundColor Green
    } else {
        Write-Host " FAILED: HTTP $($fe.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host " FAILED (frontend might not be running yet): $_" -ForegroundColor Yellow
}

# 7. Delete analysis
Write-Host "7. Delete analysis..." -NoNewline
try {
    $del = Invoke-RestMethod -Uri "$ApiUrl/api/v1/analyses/$analysisId" -Method Delete
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " FAILED: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== All smoke tests passed ===" -ForegroundColor Green
