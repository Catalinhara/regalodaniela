$baseUrl = "http://localhost:8000"
$frontendUrl = "http://localhost:5173"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "COMPREHENSIVE ENDPOINT TESTING" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test credentials
$email = "catalinohara@gmail.com"
$password = "q2ds-dt6M!EUHtG"

# --- TEST 1: Health Check ---
Write-Host "[TEST 1] Health Check Endpoint" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/health" -Method GET
    Write-Host "✓ GET /health - Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "✗ GET /health - FAILED: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# --- TEST 2: Login ---
Write-Host "[TEST 2] Login Endpoint" -ForegroundColor Yellow
try {
    $loginBody = @{
        email = $email
        password = $password
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$baseUrl/auth/login" -Method POST `
        -ContentType "application/json" `
        -Body $loginBody

    $loginData = $response.Content | ConvertFrom-Json
    $accessToken = $loginData.access_token
    $cookies = $response.Headers['Set-Cookie']

    Write-Host "✓ POST /auth/login - Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "  Access Token: $($accessToken.Substring(0, 20))..." -ForegroundColor Gray
    Write-Host "  User: $($loginData.user.email)" -ForegroundColor Gray
} catch {
    Write-Host "✗ POST /auth/login - FAILED: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "  Error Details: $responseBody" -ForegroundColor Red
    }
    $accessToken = $null
}
Write-Host ""

# Only continue if login succeeded
if ($accessToken) {
    $headers = @{
        "Authorization" = "Bearer $accessToken"
        "Content-Type" = "application/json"
    }

    # --- TEST 3: Get Current User Profile ---
    Write-Host "[TEST 3] Get Current User Profile" -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/auth/me" -Method GET -Headers $headers
        Write-Host "✓ GET /auth/me - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ GET /auth/me - FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # --- TEST 4: Get Companion Context ---
    Write-Host "[TEST 4] Get Companion Context" -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/companion/context" -Method GET -Headers $headers
        Write-Host "✓ GET /companion/context - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ GET /companion/context - FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # --- TEST 5: Submit Check-In ---
    Write-Host "[TEST 5] Submit Check-In" -ForegroundColor Yellow
    try {
        $checkInBody = @{
            context_type = "general"
            intent = "update"
            mood_state = "calm"
            energy_level = 7
            text_content = "Test check-in from endpoint testing"
        } | ConvertTo-Json

        $response = Invoke-WebRequest -Uri "$baseUrl/companion/check-in" -Method POST `
            -Headers $headers `
            -Body $checkInBody

        Write-Host "✓ POST /companion/check-in - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ POST /companion/check-in - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "  Error Details: $responseBody" -ForegroundColor Red
        }
    }
    Write-Host ""

    # --- TEST 6: List Patients ---
    Write-Host "[TEST 6] List Patients" -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/companion/patients" -Method GET -Headers $headers
        Write-Host "✓ GET /companion/patients - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ GET /companion/patients - FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # --- TEST 7: Create Patient ---
    Write-Host "[TEST 7] Create Patient" -ForegroundColor Yellow
    try {
        $patientBody = @{
            name = "Test Patient"
            age = 35
            notes = "Created during endpoint testing"
        } | ConvertTo-Json

        $response = Invoke-WebRequest -Uri "$baseUrl/companion/patients" -Method POST `
            -Headers $headers `
            -Body $patientBody

        Write-Host "✓ POST /companion/patients - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ POST /companion/patients - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "  Error Details: $responseBody" -ForegroundColor Red
        }
    }
    Write-Host ""

    # --- TEST 8: List Colleagues ---
    Write-Host "[TEST 8] List Colleagues" -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/companion/colleagues" -Method GET -Headers $headers
        Write-Host "✓ GET /companion/colleagues - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ GET /companion/colleagues - FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # --- TEST 9: Create Colleague ---
    Write-Host "[TEST 9] Create Colleague" -ForegroundColor Yellow
    try {
        $colleagueBody = @{
            name = "Test Colleague"
            role = "Nurse"
            notes = "Created during endpoint testing"
        } | ConvertTo-Json

        $response = Invoke-WebRequest -Uri "$baseUrl/companion/colleagues" -Method POST `
            -Headers $headers `
            -Body $colleagueBody

        Write-Host "✓ POST /companion/colleagues - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ POST /companion/colleagues - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "  Error Details: $responseBody" -ForegroundColor Red
        }
    }
    Write-Host ""

    # --- TEST 10: List Events ---
    Write-Host "[TEST 10] List Events" -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/companion/events" -Method GET -Headers $headers
        Write-Host "✓ GET /companion/events - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ GET /companion/events - FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # --- TEST 11: Create Event ---
    Write-Host "[TEST 11] Create Event" -ForegroundColor Yellow
    try {
        $eventBody = @{
            title = "Test Event"
            event_type = "meeting"
            notes = "Created during endpoint testing"
        } | ConvertTo-Json

        $response = Invoke-WebRequest -Uri "$baseUrl/companion/events" -Method POST `
            -Headers $headers `
            -Body $eventBody

        Write-Host "✓ POST /companion/events - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ POST /companion/events - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "  Error Details: $responseBody" -ForegroundColor Red
        }
    }
    Write-Host ""

    # --- TEST 12: Generate Insight ---
    Write-Host "[TEST 12] Generate Insight" -ForegroundColor Yellow
    try {
        $insightBody = @{} | ConvertTo-Json

        $response = Invoke-WebRequest -Uri "$baseUrl/companion/generate-insight" -Method POST `
            -Headers $headers `
            -Body $insightBody

        Write-Host "✓ POST /companion/generate-insight - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ POST /companion/generate-insight - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "  Error Details: $responseBody" -ForegroundColor Red
        }
    }
    Write-Host ""

    # --- TEST 13: Chat ---
    Write-Host "[TEST 13] Chat Endpoint" -ForegroundColor Yellow
    try {
        $chatBody = @{
            message = "Hello, this is a test message"
            history = ,@()
        } | ConvertTo-Json

        $response = Invoke-WebRequest -Uri "$baseUrl/companion/chat" -Method POST `
            -Headers $headers `
            -Body $chatBody

        Write-Host "✓ POST /companion/chat - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ POST /companion/chat - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "  Error Details: $responseBody" -ForegroundColor Red
        }
    }
    Write-Host ""

    # --- TEST 14: Logout ---
    Write-Host "[TEST 14] Logout Endpoint" -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/auth/logout" -Method POST -Headers $headers
        Write-Host "✓ POST /auth/logout - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ POST /auth/logout - FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

} else {
    Write-Host "Skipping authenticated endpoint tests due to login failure." -ForegroundColor Red
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TESTING COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
