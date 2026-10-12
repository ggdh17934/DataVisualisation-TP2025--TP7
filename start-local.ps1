# Restart the portable Metabase installation already prepared on this computer.
$ErrorActionPreference = 'Stop'
$toolsRoot = Join-Path (Split-Path $PSScriptRoot -Parent) '.task-tools'
$runtime = Join-Path $toolsRoot 'metabase-runtime'
$pgBin = Join-Path $toolsRoot 'postgresql\pgsql\bin'
$pgData = Join-Path $toolsRoot 'pg-data'
if (-not (Test-Path -LiteralPath (Join-Path $runtime 'metabase.jar'))) {
    throw 'This portable installation is unavailable. Use the included Docker Compose method.'
}
try {
    $health = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 3
    if ($health.status -eq 'ok') { Write-Output 'Metabase is already running at http://localhost:8000/dashboard/2'; return }
} catch { }
& (Join-Path $pgBin 'pg_ctl.exe') -D $pgData status | Out-Null
if ($LASTEXITCODE -ne 0) {
    & (Join-Path $pgBin 'pg_ctl.exe') -D $pgData -l (Join-Path $toolsRoot 'pg-server.log') -o '-h 127.0.0.1 -p 5446' -w start
    if ($LASTEXITCODE -ne 0) { throw 'The local application database did not start.' }
}
$env:MB_DB_TYPE = 'postgres'
$env:MB_DB_HOST = '127.0.0.1'
$env:MB_DB_PORT = '5446'
$env:MB_DB_USER = 'tp5_user'
$env:MB_DB_PASS = [IO.File]::ReadAllText((Join-Path $toolsRoot 'pg-password.txt'))
$env:MB_DB_DBNAME = 'tp7_metabase'
$env:MB_JETTY_HOST = '127.0.0.1'
$env:MB_JETTY_PORT = '8000'
$env:MB_ANON_TRACKING_ENABLED = 'false'
$env:MB_CHECK_FOR_UPDATES = 'false'
$env:MB_SITE_URL = 'http://localhost:8000'
$javaFiles = @(Get-ChildItem (Join-Path $runtime 'java') -Recurse -Filter java.exe)
if ($javaFiles.Count -ne 1) { throw 'Expected the single prepared Java runtime.' }
$server = Start-Process -FilePath $javaFiles[0].FullName -ArgumentList '-Xmx1024m','--add-opens','java.base/java.nio=ALL-UNNAMED','-jar','metabase.jar' -WorkingDirectory $runtime -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtime 'server.log') -RedirectStandardError (Join-Path $runtime 'server-error.log')
[IO.File]::WriteAllText((Join-Path $runtime 'server.pid'), [string]$server.Id)
Write-Output 'Metabase is starting. Once ready, open http://localhost:8000/dashboard/2'
