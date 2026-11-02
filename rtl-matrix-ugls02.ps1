# UGLS-02 Task 3: RTL matrix capture (servers assumed UP on :3000/:8100).
# Captures screenshots + dumped DOM, asserts lang/dir/markers/verbatim IDs.
# Usage (escalated): powershell -ExecutionPolicy Bypass -File rtl-matrix-ugls02.ps1
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$ev = Join-Path $root "rtl-evidence-ugls02"
$profile = Join-Path $root ".edge-qa-profile"
New-Item -ItemType Directory $ev -Force | Out-Null
if (Test-Path $profile) { Remove-Item $profile -Recurse -Force }
$hashBefore = (Get-FileHash data/state.json -Algorithm SHA256).Hash

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
  $err = & $edge --headless=new --disable-gpu --no-first-run --hide-scrollbars `
    --no-proxy-server --user-data-dir=$profile --window-size=$($s[2]) `
    --virtual-time-budget=15000 --screenshot=$png $s[1] 2>&1 |
    Select-String 'bytes written|ERROR' | Select-Object -First 2
  $ok = (Test-Path $png) -and (Get-Item $png).Length -gt 0
  "SHOT $($s[0]): $ok :: $($err -join ' / ')"
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
  & $edge --headless=new --disable-gpu --no-first-run --no-proxy-server `
    --user-data-dir=$profile --window-size=1440,900 `
    --virtual-time-budget=15000 --dump-dom $d[1] 2>$null |
    Set-Content $html
  if (-not (Test-Path $html)) { "DOM $($d[0]): NO OUTPUT"; continue }
  $t = Get-Content $html -Raw
  $rtl = ($t -match '<html[^>]*dir="rtl"')
  $lang = ([regex]::Match($t, '<html[^>]*lang="([^"]+)"').Groups[1].Value)
  $markers = ([regex]::Matches($t, '\[[a-z]+\.[A-Za-z0-9_.]+\]').Count)
  $arabic = ($t -match '[\u0600-\u06FF]')
  $verbatim = ($t -match 'inv_84721|txn_84721|case_84721')
  "DOM $($d[0]): len=$($t.Length) lang=$lang rtl=$rtl arabic=$arabic markers=$markers verbatim-id=$verbatim"
}
$hashAfter = (Get-FileHash data/state.json -Algorithm SHA256).Hash
"STATE_UNCHANGED:$($hashBefore -eq $hashAfter)"
Remove-Item $profile -Recurse -Force -ErrorAction SilentlyContinue
"DONE"
