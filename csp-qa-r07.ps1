# R07: CSP verification — build (:8100 QA), serve, capture Edge console
# per route, report violations, stop everything.
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$profile = Join-Path $root ".edge-csp-profile"
if (Test-Path $profile) { Remove-Item $profile -Recurse -Force }
$env:NEXT_TELEMETRY_DISABLED = "1"
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8100"
Set-Location frontend
npm run build > ..\build-csp-r07.log 2>&1
"BUILD_EXIT:$LASTEXITCODE"
Set-Location $root
$be = Start-Process .venv\Scripts\python -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8100" -PassThru -WindowStyle Hidden
$fe = Start-Process cmd -ArgumentList "/c","npm run start -- --port 3000" -WorkingDirectory "$root\frontend" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 14
"CSP_HEADER:"; (curl.exe -sI http://127.0.0.1:3000/demo | Select-String 'content-security-policy') -replace '^.{0,90}', '[truncated] '
$routes = @("/", "/demo", "/investigations/inv_84721", "/network/txn_84721",
  "/cases/case_84721", "/cases/case_84721/audit", "/replay/scn_primary",
  "/demo?locale=ar")
foreach ($r in $routes) {
  $log = & $edge --headless=new --disable-gpu --no-first-run --no-proxy-server `
    --enable-logging=stderr --log-level=0 --user-data-dir=$profile `
    --window-size=1440,900 --virtual-time-budget=12000 --dump-dom `
    ("http://127.0.0.1:3000" + $r) 2>&1 |
    Select-String 'Content Security Policy|Refused to|Uncaught|ERROR:console' |
    Select-Object -First 4
  if ($log) { "ROUTE $r VIOLATIONS:"; $log } else { "ROUTE $r CLEAN" }
}
Stop-Process -Id $be.Id,$fe.Id -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1
Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -like "*next*start*3000*" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -like "*uvicorn*8100*" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Remove-Item $profile -Recurse -Force -ErrorAction SilentlyContinue
Get-FileHash data/state.json -Algorithm SHA256 | Select-Object -ExpandProperty Hash
"DONE"
