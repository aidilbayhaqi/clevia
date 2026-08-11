$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "  Clevia Beauty Clinic - Backend Setup" -ForegroundColor Magenta
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host ""

# 1. Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker tidak ditemukan." -ForegroundColor Red
    Write-Host "Install Docker Desktop terlebih dahulu, lalu jalankan script ini lagi."
    exit 1
}

try {
    docker compose version | Out-Null
}
catch {
    Write-Host "[ERROR] Docker Compose v2 tidak tersedia." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Docker dan Docker Compose tersedia." -ForegroundColor Green

# 2. Prepare .env
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] File .env dibuat dari .env.example." -ForegroundColor Green
}
else {
    Write-Host "[INFO] File .env sudah ada, tidak ditimpa." -ForegroundColor Yellow
}

# 3. Generate JWT secret if placeholder still exists
$envContent = Get-Content ".env" -Raw

if ($envContent -match "JWT_SECRET=replace-with-a-long-random-secret") {
   $bytes = New-Object byte[] 48

$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()

try {
    $rng.GetBytes($bytes)
}
finally {
    $rng.Dispose()
}

$jwtSecret = [Convert]::ToBase64String($bytes)

    $envContent = $envContent.Replace(
        "JWT_SECRET=replace-with-a-long-random-secret",
        "JWT_SECRET=$jwtSecret"
    )

    Set-Content ".env" $envContent -Encoding UTF8

    Write-Host "[OK] JWT_SECRET random berhasil dibuat." -ForegroundColor Green
}

# 4. Warn if OpenAI key is missing
$envContent = Get-Content ".env" -Raw

if ($envContent -match "(?m)^OPENAI_API_KEY=$") {
    Write-Host ""
    Write-Host "[ACTION REQUIRED] OPENAI_API_KEY masih kosong." -ForegroundColor Yellow
    Write-Host "Buka file .env dan isi:"
    Write-Host "OPENAI_API_KEY=sk-..."
    Write-Host ""
    Write-Host "Backend tetap bisa dibuild, tetapi chatbot AI tidak akan berfungsi sampai key diisi."
    Write-Host ""
}

# 5. Build containers
Write-Host "[1/3] Building Docker images..." -ForegroundColor Cyan
docker compose build

# 6. Start stack
Write-Host "[2/3] Starting Clevia backend..." -ForegroundColor Cyan
docker compose up -d

# 7. Seed demo data
Write-Host "[3/3] Seeding Clevia demo data..." -ForegroundColor Cyan

$maxAttempts = 20
$attempt = 0
$apiReady = $false

while ($attempt -lt $maxAttempts) {
    $attempt++

    try {
        $status = docker compose ps --status running --services

        if ($status -contains "api") {
            $apiReady = $true
            break
        }
    }
    catch {
    }

    Start-Sleep -Seconds 2
}

if (-not $apiReady) {
    Write-Host "[WARN] API belum terdeteksi running. Cek logs dengan:" -ForegroundColor Yellow
    Write-Host "docker compose logs -f api"
}
else {
    docker compose exec -T api python -m scripts.seed
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Setup selesai" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Swagger API : http://localhost:8000/docs"
Write-Host "Health      : http://localhost:8000/api/v1/health/ready"
Write-Host ""
Write-Host "Demo CRM Login:"
Write-Host "Email    : owner@clevia.local"
Write-Host "Password : ChangeMe123!"
Write-Host ""
Write-Host "PENTING:"
Write-Host "- Ganti password demo sebelum deployment nyata."
Write-Host "- Isi OPENAI_API_KEY di .env untuk mengaktifkan chatbot."
Write-Host ""
Write-Host "Commands:"
Write-Host "docker compose ps"
Write-Host "docker compose logs -f api"
Write-Host "docker compose down"
Write-Host ""
