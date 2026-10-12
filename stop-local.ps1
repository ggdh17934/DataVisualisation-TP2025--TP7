# Stop only this coursework installation; preserve its application database.
$ErrorActionPreference = 'Stop'
$toolsRoot = Join-Path (Split-Path $PSScriptRoot -Parent) '.task-tools'
$runtime = Join-Path $toolsRoot 'metabase-runtime'
$pidFile = Join-Path $runtime 'server.pid'
if (Test-Path -LiteralPath $pidFile) {
    $serverId = [int][IO.File]::ReadAllText($pidFile)
    $server = Get-CimInstance Win32_Process -Filter "ProcessId=$serverId"
    if ($server) {
        if ($server.CommandLine -notmatch 'metabase\.jar' -or $server.ExecutablePath -notlike "$runtime\java\*") {
            throw 'The saved process no longer matches this Metabase installation; not stopping it.'
        }
        Stop-Process -Id $serverId
    }
}
& (Join-Path $toolsRoot 'postgresql\pgsql\bin\pg_ctl.exe') -D (Join-Path $toolsRoot 'pg-data') -w stop
Write-Output 'The local Metabase installation is stopped; the saved dashboard is preserved.'
