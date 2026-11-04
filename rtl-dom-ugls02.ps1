# UGLS-02 Task 3: DOM re-capture with UTF-8 (servers assumed UP).
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$ev = Join-Path $root "rtl-evidence-ugls02"
$profile = Join-Path $root ".edge-qa-profile2"
if (Test-Path $profile) { Remove-Item $profile -Recurse -Force }
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
    Set-Content $html -Encoding utf8
  $t = Get-Content $html -Raw -Encoding utf8
  $rtl = ($t -match '<html[^>]*dir="rtl"')
  $lang = ([regex]::Match($t, '<html[^>]*lang="([^"]+)"').Groups[1].Value)
  $markers = ([regex]::Matches($t, '\[[a-z]+\.[A-Za-z0-9_.]+\]').Count)
  $arabic = ($t -match '[\u0600-\u06FF]')
  $verbatim = ($t -match 'inv_84721|txn_84721|case_84721')
  "DOM $($d[0]): len=$($t.Length) lang=$lang rtl=$rtl arabic=$arabic markers=$markers verbatim-id=$verbatim"
}
Remove-Item $profile -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $ev "demo-ar-utf8.html") -ErrorAction SilentlyContinue
"DONE"
