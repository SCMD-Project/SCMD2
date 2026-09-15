param(
    [string]$Scmdc,
    [string]$Project
)

$ErrorActionPreference = 'Stop'

# Resolve scmdc.
if (-not $Scmdc) {
    if ($env:SCMDC) {
        $Scmdc = $env:SCMDC
    }
    else {
        $cmd = Get-Command scmdc -ErrorAction SilentlyContinue
        if ($cmd) {
            $Scmdc = $cmd.Source
        }
    }
}

if (-not $Scmdc) {
    throw @"
scmdc was not found.

Add scmdc to PATH, set SCMDC, or specify it manually:

    .\build.ps1 -Scmdc C:\path\to\scmdc.exe
"@
}

if (-not (Test-Path $Scmdc -PathType Leaf)) {
    $cmd = Get-Command $Scmdc -ErrorAction SilentlyContinue
    if ($cmd) {
        $Scmdc = $cmd.Source
    }
    else {
        throw "scmdc not found: $Scmdc"
    }
}

# Resolve project.
if (-not $Project) {
    $projects = @(Get-ChildItem -File -Filter *.scmdproj)

    if ($projects.Count -eq 0) {
        throw "No .scmdproj file found in the current directory."
    }

    if ($projects.Count -gt 1) {
        $names = ($projects.Name -join ', ')
        throw "Multiple .scmdproj files found: $names`nUse -Project <file>."
    }

    $Project = $projects[0].FullName
}

Write-Host "[SCMD] Compiler: $Scmdc"
Write-Host "[SCMD] Project:  $Project"
Write-Host ""

& $Scmdc build $Project

if ($LASTEXITCODE -ne 0) {
    throw "SCMD build failed with exit code $LASTEXITCODE."
}