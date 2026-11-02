# UGLS-02 Task 3: RTL browser verification (Edge headless).
# Serves backend (open-demo, GET only) + production frontend build,
# captures screenshots + dumped DOM for ar/ha-Arab/fr/en at 3 viewports,
# asserts lang/dir/markers/verbatim IDs, then stops everything.
# Usage (escalated): powershell -ExecutionPolicy Bypass -File rtl-qa-ugls02.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$ev = Join-Path $root "rtl-evidence-ugls02"
$profile = Join-Path $root ".edge-qa-profile"
New-Item -ItemType Directory $ev -Force | Out-Null
if (Test-Path $profile) { Remove-Item $profile -Recurse -Force }
$hashBefore = (Get-FileHash data/state.json -Algorithm SHA256).Hash

$be = Start-Process .venv\Scripts\python `
  -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" `
  -PassThru -WindowStyle Hidden
$fe = Start-Process cmd -ArgumentList "/c","npm run start -- --port 3000 > ..\fe-qa.log 2>&1" `
  -WorkingDirectory (Join-Path $root "frontend") -PassThru -WindowStyle Hidden

function Wait-Url($url, $tries) {
  for ($i = 0; $i -lt $tries; $i++) {
    try { if ((Invoke-WebRequest $url -TimeoutSec 3).StatusCode -eq 200) { return $true } }
    catch { Start-Sleep -Seconds 2 }
  }
  return $false
}
$beOk = Wait-Url "http://127.0.0.1:8000/api/v1/health" 30
$feOk = Wait-Url "http://127.0.0.1:3000/" 45
"BACKEND_UP:$beOk FRONTEND_UP:$feOk"
if (-not ($beOk -and $feOk)) {
  Stop-Process -Id $be.Id,$fe.Id -Force -ErrorAction SilentlyContinue
  throw "servers did not start"
}

$shots = @(
  @("home-ar","http://127.0.0.1:3000/?locale=ar","1440,900"),
  @("home-ar-mob","http://127.0.0.1:3000/?locale=ar","390,844"),
  @("home-ar-tab","http://127.0.0.1:3000/?locale=ar","768,1024"),
  @("demo-ar","http://127.0.0.1:3000/demo?locale=ar","1440,900"),
  @("demo-ar-mob","http://127.0.0.1:3000/demo?locale=ar","390,844"),
  @("inv-ar","http://127.0.0.1:3000/investigations/inv_84721?locale=ar","1440,900"),
  @("inv-ar-mob","http://127.0.0.1:3000/investigations/inv_84721?locale=ar","390,844"),
  @("net-ar","http://127.0.0.1:3000/network/txn_84721?locale=ar","1440,900"),
  @("case-ar","http://127.0.0.1:3000/cases/case_84721?locale=ar","1440,900"),
  @("audit-ar","http://127.0.0.1:3000/cases/case_84721/audit?locale=ar","1440,900"),
  @("replay-ar","http://127.0.0.1:3000/replay/scn_primary?locale=ar","1440,900"),
  @("demo-ha-Arab","http://127.0.0.1:3000/demo?locale=ha-Arab","1440,900"),
  @("demo-fr","http://127.0.0.1:3000/demo?locale=fr","1440,900"),
  @("demo-en","http://127.0.0.1:3000/demo","1440,900")
)
foreach ($s in $shots) {
  $png = Join-Path $ev ($s[0] + ".png")
  & $edge --headless=new --disable-gpu --no-first-run --hide-scrollbars `
    --user-data-dir=$profile --window-size=$($s[2]) `
    --virtual-time-budget=15000 --screenshot=$png $s[1] 2>$null
  "SHOT $($s[0]): $((Test-Path $png) -and (Get-Item $png).Length -gt 0)"
}
$doms = @(
  @("demo-ar","http://127.0.0.1:3000/demo?locale=ar"),
  @("inv-ar","http://127.0.0.1:3000/investigations/inv_84721?locale=ar"),
  @("net-ar","http://127.0.0.1:3000/network/txn_84721?locale=ar"),
  @("case-ar","http://127.0.0.1:3000/cases/case_84721?locale=ar"),
  @("audit-ar","http://127.0.0.1:3000/cases/case_84721/audit?locale=ar"),
  @("replay-ar","http://127.0.0.1:3000/replay/scn_primary?locale=ar"),
  @("demo-ha-Arab","http://127.0.0.1:3000/demo?locale=ha-Arab"),
  @("demo-fr","http://127.0.0.1:3000/demo?locale=fr")
)
foreach ($d in $doms) {
  $html = Join-Path $ev ($d[0] + ".html")
  & $edge --headless=new --disable-gpu --no-first-run `
    --user-data-dir=$profile --window-size=1440,900 `
    --virtual-time-budget=15000 --dump-dom $d[1] 2>$null | Set-Content $html
  $t = Get-Content $html -Raw
  $rtl = ($t -match '<html[^>]*dir="rtl"')
  $markers = ([regex]::Matches($t, '\[[a-z]+\.[A-Za-z0-9_.]+\]').Count)
  $arabic = ($t -match '[\u0600-\u06FF]')
  $verbatim = ($t -match 'inv_84721')
  "DOM $($d[0]): len=$($t.Length) rtl=$rtl arabic=$arabic markers=$markers verbatim-id=$verbatim"
}
Stop-Process -Id $be.Id,$fe.Id -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1
Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -like "*next-server*" -and $_.CommandLine -like "*3000*" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -like "*uvicorn*" -and $_.CommandLine -like "*8000*" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
$hashAfter = (Get-FileHash data/state.json -Algorithm SHA256).Hash
"STATE_UNCHANGED:$($hashBefore -eq $hashAfter)"
Remove-Item $profile -Recurse -Force -ErrorAction SilentlyContinue
"DONE"
