# PowerShell script to fix git and push to GitHub
# Run this in PowerShell as Administrator

Write-Host "==========================================" -ForegroundColor Green
Write-Host "AI Fact Checker - Git Fix Script" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 1. Remove any existing .git repos in wrong places
Write-Host "`n[1/6] Cleaning up incorrectly placed git repositories..." -ForegroundColor Yellow
$homeGit = "$env:USERPROFILE\.git"
if (Test-Path $homeGit) {
    Remove-Item -Recurse -Force $homeGit
    Write-Host "   Removed .git from home directory" -ForegroundColor Green
} else {
    Write-Host "   No .git found in home directory" -ForegroundColor Gray
}

# 2. Navigate to the correct folder
$projectPath = "G:\mnt\c\Users\noah7\CascadeProjects\AI Fact Checker"
Write-Host "`n[2/6] Navigating to project folder..." -ForegroundColor Yellow
if (Test-Path $projectPath) {
    Set-Location $projectPath
    Write-Host "   Now in: $projectPath" -ForegroundColor Green
} else {
    Write-Host "   ERROR: Project folder not found at $projectPath" -ForegroundColor Red
    exit 1
}

# 3. Remove existing .git in project folder if any
Write-Host "`n[3/6] Removing existing git repository in project folder..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Remove-Item -Recurse -Force .git
    Write-Host "   Removed old .git folder" -ForegroundColor Green
} else {
    Write-Host "   No existing .git folder" -ForegroundColor Gray
}

# 4. Initialize fresh git repo
Write-Host "`n[4/6] Initializing fresh git repository..." -ForegroundColor Yellow
git init
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR: git init failed" -ForegroundColor Red
    exit 1
}
Write-Host "   Git repository initialized" -ForegroundColor Green

# 5. Configure git user
Write-Host "`n[5/6] Configuring git user..." -ForegroundColor Yellow
git config user.email "noah@example.com"
git config user.name "MONKE2525E"
Write-Host "   Git user configured" -ForegroundColor Green

# 6. Add files, commit and push
Write-Host "`n[6/6] Adding files and pushing to GitHub..." -ForegroundColor Yellow

git add .
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR: git add failed" -ForegroundColor Red
    exit 1
}
Write-Host "   Files added" -ForegroundColor Green

git commit -m "Initial commit: AI Fact Checker bot with startup script"
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR: git commit failed" -ForegroundColor Red
    exit 1
}
Write-Host "   Changes committed" -ForegroundColor Green

git remote add origin https://github.com/MONKE2525E/Discord-Bot-AI-Fact-Checker-Vibe-Coded.git 2>$null
git branch -M main
git push -u origin main --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR: git push failed" -ForegroundColor Red
    Write-Host "   You may need to authenticate with GitHub" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "SUCCESS! Project pushed to GitHub!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

Pause
