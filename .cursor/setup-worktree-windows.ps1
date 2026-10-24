# Cursor worktree setup (Windows). Every worktree shares one venv (D:\duq-venv, created by
# docs/plan/briefs/00-setup.md), so here we only verify that it imports this worktree's code.
$py = if ($env:DUQ_PY) { $env:DUQ_PY } else { "D:\duq-venv\Scripts\python.exe" }
if (-not (Test-Path $py)) {
    Write-Host "[setup] Shared venv not found at $py. Run docs/plan/briefs/00-setup.md first, or set DUQ_PY."
    exit 1
}
& $py -c "from src import config as C; import dynamiqs as dq; print('[setup] OK dynamiqs', dq.__version__, '| kappa_2/2pi =', round(C.KAPPA_2 / C.TWO_PI, 3), 'MHz (expect 0.896)')"
if ($LASTEXITCODE -ne 0) { exit 1 }
# The Lab lane installs its own node_modules inside site/ (npm ci); nothing to do here.
