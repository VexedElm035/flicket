# Escaneo automatico de Flicket con pip-audit (SCA), Bandit y Semgrep (SAST).
# Cada herramienta corre en un contenedor desechable (--rm) con el codigo montado en solo lectura (:ro).
# Se analiza exactamente el commit indicado (git archive), sin archivos no versionados del arbol de trabajo.
#
# Uso (desde la raiz del repositorio):
#   pwsh security/scripts/run_scans.ps1                                    # linea base adcc3f6
#   pwsh security/scripts/run_scans.ps1 -Commit mitigaciones -Out security/evidencias/scans_mitigaciones
#
# Requisitos: git, tar y Docker.

param(
    [string]$Repo = ".",
    [string]$Out = "security/evidencias/scans_linea_base",
    [string]$Commit = "adcc3f60057ea09872f033b9364ce74a11113253"
)

$ErrorActionPreference = "Stop"
$Sha = (git -C $Repo rev-parse $Commit).Trim()
$Out = (New-Item -ItemType Directory -Force $Out).FullName
$Src = Join-Path ([System.IO.Path]::GetTempPath()) "flicket_scan_$($Sha.Substring(0,7))"

# 1. Exportar el commit.
if (Test-Path $Src) { Remove-Item -Recurse -Force $Src -Confirm:$false }
New-Item -ItemType Directory $Src | Out-Null
git -C $Repo archive --format=tar $Sha -o "$Src.tar"
tar -xf "$Src.tar" -C $Src
Remove-Item "$Src.tar"
Set-Content -Path (Join-Path $Out "commit.txt") -Value $Sha

# 2. pip-audit (SCA) sobre requirements.txt
docker run --rm -v "${Src}:/src:ro" -v "${Out}:/out" python:3.11-slim sh -c `
  "pip install -q --root-user-action=ignore pip-audit==2.9.0 >/dev/null 2>&1; pip-audit --version > /out/pip-audit_version.txt; cd /src && pip-audit -r requirements.txt --desc on -f json -o /out/pip-audit.json; pip-audit -r requirements.txt -f columns -o /out/pip-audit.txt; true"

# 3. Bandit (SAST Python) sobre el paquete application/ y config.py
docker run --rm -v "${Src}:/src:ro" -v "${Out}:/out" python:3.11-slim sh -c `
  "pip install -q --root-user-action=ignore bandit==1.8.6 >/dev/null 2>&1; bandit --version | head -1 > /out/bandit_version.txt; cd /src && bandit -r application config.py -f json -o /out/bandit.json -q; bandit -r application config.py -f txt -o /out/bandit.txt -q; true"

# 4. Semgrep (SAST Python + plantillas Jinja2); se excluyen las librerias JS de terceros en static/
$rules = "--config p/python --config p/flask --config p/secrets --config p/xss --config r/python.flask " +
         "--config r/python.lang.security --config r/generic.html-templates --config r/python.sqlalchemy"
docker run --rm -v "${Src}:/src:ro" -v "${Out}:/out" semgrep/semgrep:1.140.0 sh -c `
  "semgrep --version > /out/semgrep_version.txt; cd /src && semgrep scan --metrics=off $rules --exclude application/flicket/static --exclude security --json -o /out/semgrep.json . ; semgrep scan --metrics=off $rules --exclude application/flicket/static --exclude security --text -o /out/semgrep.txt . ; true"

Remove-Item -Recurse -Force $Src -Confirm:$false
Write-Output "Commit $Sha analizado. Resultados en $Out"
