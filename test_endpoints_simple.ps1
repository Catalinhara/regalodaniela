# Comprehensive Endpoint Testing Script
$baseUrl = "http://localhost:8000"
$email = "catalinohara@gmail.com"
$password = "q2ds-dt6M!EUHtG"

Write-Host "========================================"
Write-Host "COMPREHENSIVE ENDPOINT TESTING"
Write-Host "========================================"
Write-Host ""

# TEST 1: Health Check
Write-Host "[TEST 1] Health Check" -ForegroundColor Yellow
try {
    $r = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "SUCCESS - Status: healthy" -ForegroundColor Green
    Write-Host "Response: $($r | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# TEST 2: Login
Write-Host "[TEST 2] Login" -ForegroundColor Yellow
try {
    $loginJson = "{`"email`":`"$email`",`"password`":`"$password`"}"
    $r = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method POST -Body $loginJson -ContentType "application/json"
    $token = $r.access_token
    Write-Host "SUCCESS - Got access token" -ForegroundColor Green
    Write-Host "User: $($r.user.email)" -ForegroundColor Gray
    
    # Save token for next tests
    $global:authHeader = @{ Authorization = "Bearer $token" }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $global:authHeader = $null
}
Write-Host ""

if ($global:authHeader) {
    # TEST 3: Get User Profile
    Write-Host "[TEST 3] Get User Profile (/auth/me)" -ForegroundColor Yellow
    try {
        $r = Invoke-RestMethod -Uri "$baseUrl/auth/me" -Method GET -Headers $global:authHeader
        Write-Host "SUCCESS" -ForegroundColor Green
        Write-Host "User: $($r.email), ID: $($r.id)" -ForegroundColor Gray
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # TEST 4: Get Companion Context
    Write-Host "[TEST 4] Get Companion Context" -ForegroundColor Yellow
    try {
        $r = Invoke-RestMethod -Uri "$baseUrl/companion/context" -Method GET -Headers $global:authHeader
        Write-Host "SUCCESS" -ForegroundColor Green
        Write-Host "Context ID: $($r.id)" -ForegroundColor Gray
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # TEST 5: List Patients
    Write-Host "[TEST 5] List Patients" -ForegroundColor Yellow
    try {
        $r = Invoke-RestMethod -Uri "$baseUrl/companion/patients" -Method GET -Headers $global:authHeader
        Write-Host "SUCCESS - Found $($r.Count) patients" -ForegroundColor Green
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # TEST 6: Create Patient
    Write-Host "[TEST 6] Create Patient" -ForegroundColor Yellow
    try {
        $patientJson = '{"name":"Test Patient Automated", "age":42, "notes":"From automated test"}'
        $headers = $global:authHeader.Clone()
        $headers['Content-Type'] = 'application/json'
        $r = Invoke-RestMethod -Uri "$baseUrl/companion/patients" -Method POST -Headers $headers -Body $patientJson
        Write-Host "SUCCESS - Created patient: $($r.name)" -ForegroundColor Green
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # TEST 7: List Colleagues
    Write-Host "[TEST 7] List Colleagues" -ForegroundColor Yellow
    try {
        $r = Invoke-RestMethod -Uri "$baseUrl/companion/colleagues" -Method GET -Headers $global:authHeader
        Write-Host "SUCCESS - Found $($r.Count) colleagues" -ForegroundColor Green
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # TEST 8: Create Colleague
    Write-Host "[TEST 8] Create Colleague" -ForegroundColor Yellow
    try {
        $colleagueJson = '{"name":"Test Colleague Automated", "role":"Doctor", "notes":"From automated test"}'
        $headers = $global:authHeader.Clone()
        $headers['Content-Type'] = 'application/json'
        $r = Invoke-RestMethod -Uri "$baseUrl/companion/colleagues" -Method POST -Headers $headers -Body $colleagueJson
        Write-Host "SUCCESS - Created colleague: $($r.name)" -ForegroundColor Green
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # TEST 9: List Events
    Write-Host "[TEST 9] List Events" -ForegroundColor Yellow
    try {
        $r = Invoke-RestMethod -Uri "$baseUrl/companion/events" -Method GET -Headers $global:authHeader
        Write-Host "SUCCESS - Found $($r.Count) events" -ForegroundColor Green
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # TEST 10: Create Event
    Write-Host "[TEST 10] Create Event" -ForegroundColor Yellow
    try {
        $eventJson = '{"title":"Test Event Automated", "event_type":"meeting", "notes":"From automated test"}'
        $headers = $global:authHeader.Clone()
        $headers['Content-Type'] = 'application/json'
        $r = Invoke-RestMethod -Uri "$baseUrl/companion/events" -Method POST -Headers $headers -Body $eventJson
        Write-Host "SUCCESS - Created event: $($r.title)" -ForegroundColor Green
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # TEST 11: Submit Check-In
    Write-Host "[TEST 11] Submit Check-In" -ForegroundColor Yellow
    try {
        $checkInJson = '{"context_type":"general","intent":"update","mood_state":"calm","energy_level":7,"text_content":"Automated test check-in"}'
        $headers = $global:authHeader.Clone()
        $headers['Content-Type'] = 'application/json'
        $r = Invoke-RestMethod -Uri "$baseUrl/companion/check-in" -Method POST -Headers $headers -Body $checkInJson
        Write-Host "SUCCESS - Check-in recorded" -ForegroundColor Green
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # TEST 12: Chat
    Write-Host "[TEST 12] Chat" -ForegroundColor Yellow
    try {
        $chatJson = '{"message":"Hello, this is a test","history":[]}'
        $headers = $global:authHeader.Clone()
        $headers['Content-Type'] = 'application/json'
        $r = Invoke-RestMethod -Uri "$baseUrl/companion/chat" -Method POST -Headers $headers -Body $chatJson
        Write-Host "SUCCESS - Got chat response" -ForegroundColor Green
        Write-Host "Response: $($r.content.Substring(0, [Math]::Min(50, $r.content.Length)))..." -ForegroundColor Gray
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""

    # TEST 13: Logout
    Write-Host "[TEST 13] Logout" -ForegroundColor Yellow
    try {
        $r = Invoke-RestMethod -Uri "$baseUrl/auth/logout" -Method POST -Headers $global:authHeader
        Write-Host "SUCCESS - $($r.message)" -ForegroundColor Green
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
    
} else {
    Write-Host "Skipping authenticated tests due to login failure" -ForegroundColor Red
}

Write-Host "========================================"
Write-Host "TESTING COMPLETE"
Write-Host "========================================"
