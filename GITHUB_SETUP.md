# GitHub Setup Instructions

This project is ready to be published to GitHub. Here's how:

## Step 1: Create a GitHub Repository

1. Go to https://github.com/new
2. Repository name: `tiktok-fact-checker` (or any name you prefer)
3. Make it Public or Private (your choice)
4. **DO NOT** initialize with README, .gitignore, or License (we already have these files)
5. Click "Create repository"

## Step 2: Push Your Code

Open a terminal in your project folder and run:

```bash
# Navigate to your project folder
cd /mnt/c/Users/noah7/CascadeProjects

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: TikTok/YouTube/Instagram Fact Checker Bot"

# Add the remote repository (replace with your actual GitHub URL)
git remote add origin https://github.com/YOUR_USERNAME/tiktok-fact-checker.git

# Push to GitHub
git push -u origin main
```

## What's Included

The repository contains:

- ✅ `tiktok_factcheck.py` - Main bot code
- ✅ `requirements.txt` - Python dependencies
- ✅ `tiktok_factcheck_config.json` - Config template (sanitized)
- ✅ `Dockerfile` - Docker configuration
- ✅ `docker-compose.yml` - Docker Compose setup
- ✅ `README.md` - Documentation
- ✅ `.gitignore` - Git ignore rules
- ✅ `.dockerignore` - Docker ignore rules

## ⚠️ IMPORTANT: Secrets Removed

For security, I've replaced your actual secrets with placeholders:

- Discord Webhook URL → `YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN`
- Gemini API Key → `YOUR_GEMINI_API_KEY_HERE`
- Discord Bot Token → `YOUR_DISCORD_BOT_TOKEN_HERE`
- Channel ID → `YOUR_CHANNEL_ID_HERE`

**Keep your real config file private!** The `.gitignore` file prevents it from being committed.

## After Pushing to GitHub

1. **Copy your real config back** to run the bot locally:
   - Replace the placeholder values in `tiktok_factcheck_config.json` with your real secrets

2. **Test the bot** to make sure it still works:
   ```bash
   python tiktok_factcheck.py
   ```

3. **Optional**: If you want to run in Docker:
   ```bash
   docker-compose up -d
   ```

## Keeping Secrets Safe

- ✅ The `.gitignore` file prevents `tiktok_factcheck_config.json` from being committed
- ✅ Real secrets are NOT in the GitHub repository
- ✅ Only YOU have the real config file locally

## Updating the Bot

When you make changes and want to push updates:

```bash
git add .
git commit -m "Description of changes"
git push
```

Your config file with real secrets will NOT be pushed thanks to `.gitignore`.

## Need Help?

If you need to recover your real secrets, check your Discord Developer Portal and Google AI Studio for:
- Discord Bot Token
- Gemini API Key
- Discord Webhook URL
- Channel ID
