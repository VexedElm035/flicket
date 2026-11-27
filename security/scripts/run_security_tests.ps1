# Pruebas de regresion de las mitigaciones (H-01, H-04, H-05) en contenedores desechables.
# El repositorio se monta en solo lectura; solo se instalan las dependencias que usa cada modulo.
#
# Uso (desde la raiz del repositorio, en la rama mitigaciones):
#   pwsh security/scripts/run_security_tests.ps1
#
# Requisitos: Docker.

param(
    [string]$Repo = ".",
    [string]$Out = "security/evidencias/pruebas"
)

$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path $Repo).Path
$Out = (New-Item -ItemType Directory -Force $Out).FullName
$Sha = (git -C $Repo rev-parse HEAD).Trim()

# H-01 y falla segura de H-05: filtro |markdown con sanitizacion por lista blanca.
docker run --rm -v "${Repo}:/repo:ro" python:3.11-slim sh -c `
  "pip install -q --root-user-action=ignore markdown==3.8.2 nh3==0.3.8 markupsafe >/dev/null 2>&1; python -I /repo/security/tests/test_markdown_render.py /repo/application/flicket/scripts/markdown_render.py" |
  Tee-Object -FilePath (Join-Path $Out "h01_markdown_render.txt")

# H-04: enlace firmado de restablecimiento.
docker run --rm -v "${Repo}:/repo:ro" python:3.11-slim sh -c `
  "pip install -q --root-user-action=ignore itsdangerous==2.2.0 >/dev/null 2>&1; python -I /repo/security/tests/test_password_reset_token.py /repo/application/flicket/scripts/password_reset.py" |
  Tee-Object -FilePath (Join-Path $Out "h04_password_reset_token.txt")

# H-05: matriz de versiones de CPython y Markdown (antes: 3.5.1; despues: 3.8.2).
$matrix = Join-Path $Out "h05_markdown_cve_matriz.txt"
Set-Content -Path $matrix -Value "# CVE-2025-69534: entrada '<![' por version de CPython y de Markdown"
foreach ($py in "3.11.13", "3.11.14") {
    foreach ($md in "3.5.1", "3.8.2") {
        docker run --rm -v "${Repo}:/repo:ro" "python:$py-slim" sh -c `
          "pip install -q --root-user-action=ignore markdown==$md >/dev/null 2>&1; python -I /repo/security/tests/check_markdown_cve.py" |
          Tee-Object -FilePath $matrix -Append
    }
}

Set-Content -Path (Join-Path $Out "commit.txt") -Value $Sha
Write-Output "Pruebas del commit $Sha. Resultados en $Out"
