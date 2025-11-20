# test_postgres.ps1
try {
    python test_postgres.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Tous les tests PostgreSQL ont réussi" -ForegroundColor Green
    } else {
        Write-Host "❌ Les tests PostgreSQL ont échoué" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Erreur : $_" -ForegroundColor Red
    exit 1
}