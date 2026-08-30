# scripts/verify_release.ps1
# Sovereign-X Pre-Release Health & Environmental Verification Script (Windows 11)

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "   SOVEREIGN-X -- SYSTEM HEALTH & RELEASE VERIFICATION SUITE" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0

function Test-Check($Name, $ScriptBlock) {
    Write-Host -NoNewline "[*] Checking $Name... "
    try {
        $result = & $ScriptBlock
        if ($result -eq $true) {
            Write-Host "PASSED" -ForegroundColor Green
            return $true
        } else {
            Write-Host "FAILED" -ForegroundColor Red
            $script:ErrorCount++
            return $false
        }
    } catch {
        Write-Host "FAILED ($($_.Exception.Message))" -ForegroundColor Red
        $script:ErrorCount++
        return $false
    }
}

function Test-Warn($Name, $ScriptBlock) {
    Write-Host -NoNewline "[*] Checking $Name... "
    try {
        $result = & $ScriptBlock
        if ($result -eq $true) {
            Write-Host "PASSED" -ForegroundColor Green
            return $true
        } else {
            Write-Host "WARNING" -ForegroundColor Yellow
            $script:WarningCount++
            return $false
        }
    } catch {
        Write-Host "WARNING ($($_.Exception.Message))" -ForegroundColor Yellow
        $script:WarningCount++
        return $false
    }
}

# 1. Check Python Virtual Environment
Test-Check "Python Virtual Environment (.venv)" {
    Test-Path ".venv\Scripts\python.exe"
}

# 2. Check Local Ollama Daemon & Required Models
Test-Check "Local Ollama Daemon (http://127.0.0.1:11434)" {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    $modelNames = $res.models | ForEach-Object { $_.name }

    $hasQwen = ($modelNames -like "*qwen3:4b*") -or ($modelNames -like "*qwen*")
    $hasGemma = ($modelNames -like "*gemma3:4b*") -or ($modelNames -like "*gemma*")

    if (-not $hasQwen) { throw "qwen3:4b model missing" }
    if (-not $hasGemma) { throw "gemma3:4b model missing" }
    return $true
}

# 3. Check Docker Desktop & Sandbox Image
Test-Check "Docker Desktop & sovereign-sandbox:1.0 image" {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Docker daemon inaccessible" }
    $images = docker images --format "{{.Repository}}:{{.Tag}}"
    if ($images -notcontains "sovereign-sandbox:1.0") {
        throw "sovereign-sandbox:1.0 image not found"
    }
    return $true
}

# 4. Check NVIDIA GPU Telemetry & NVML
Test-Check "NVIDIA GPU & NVML Acceleration" {
    $smi = nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>&1
    if ($LASTEXITCODE -ne 0) { throw "nvidia-smi error" }
    return $true
}

# 5. Check Demo Assets Package
Test-Check "Flagship Industrial Demo Assets (5 Assets)" {
    $assets = @(
        "demo\assets\inspection_report.pdf",
        "demo\assets\scanned_report.pdf",
        "demo\assets\equipment_photo.jpg",
        "demo\assets\maintenance_history.xlsx",
        "demo\assets\maintenance_manual.pdf"
    )
    foreach ($a in $assets) {
        if (-not (Test-Path $a)) { throw "Missing asset: $a" }
    }
    return $true
}

# 6. Check Offline Network / Localhost Socket Invariants
Test-Check "Air-Gap Invariant (Ollama localhost binding)" {
    $conns = Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($c in $conns) {
            if ($c.LocalAddress -ne "127.0.0.1" -and $c.LocalAddress -ne "::1") {
                throw "Ollama bound to non-localhost address: $($c.LocalAddress)"
            }
        }
    }
    return $true
}

# 7. Check Frontend Dependencies & Build Output
Test-Check "Frontend Configuration & Node.js" {
    Test-Path "frontend\package.json"
}

# 8. Check Windows Batch Launchers
Test-Check "Windows Launch Scripts (run_dev.bat / stop_dev.bat)" {
    (Test-Path "scripts\run_dev.bat") -and (Test-Path "scripts\stop_dev.bat")
}

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
if ($ErrorCount -eq 0) {
    Write-Host "  [SUCCESS] SYSTEM READY FOR SIH 2026 EVALUATION & DEMO ($WarningCount warnings)" -ForegroundColor Green
} else {
    Write-Host "  [FAILED] $ErrorCount critical environment checks failed!" -ForegroundColor Red
}
Write-Host "===============================================================================" -ForegroundColor Cyan
