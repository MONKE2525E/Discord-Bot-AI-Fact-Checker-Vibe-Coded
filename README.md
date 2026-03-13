# TikTok/YouTube/Instagram Fact Checker Bot

**⚠️ NOTE: This bot was custom-coded specifically for personal use and may require modifications for general use.**

A Discord bot that automatically fact-checks TikTok videos, YouTube Shorts, and Instagram Reels using AI (Gemini API).

## Features

- 🔍 **Automatic Fact-Checking**: Detects video links in Discord messages and provides AI-powered fact-checks
- 📱 **Multi-Platform Support**: Works with TikTok, YouTube Shorts, and Instagram Reels
- 🤖 **Discord Integration**: Responds in real-time to messages in your Discord server
- 🧠 **AI-Powered Analysis**: Uses Google's Gemini API to analyze video content and claims

## Setup

### Prerequisites

- Python 3.10+
- Discord Bot Token
- Gemini API Key
- Docker (optional)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd tiktok-fact-checker
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure the bot:**
Edit `tiktok_factcheck_config.json`:
```json
{
  "discord_webhook": "YOUR_DISCORD_WEBHOOK_URL",
  "gemini_api_key": "YOUR_GEMINI_API_KEY",
  "discord_bot_token": "YOUR_BOT_TOKEN",
  "discord_channel_id": "YOUR_CHANNEL_ID"
}
```

### Getting API Keys

**Discord Bot Token:**
1. Go to https://discord.com/developers/applications
2. Create New Application → Bot
3. Copy the Bot Token
4. Enable "MESSAGE CONTENT INTENT" in Bot settings

**Gemini API Key:**
1. Go to https://aistudio.google.com/app/apikey
2. Create API Key

**Discord Channel ID:**
1. Enable Developer Mode in Discord (Settings → Advanced)
2. Right-click channel → Copy Channel ID

## Running the Bot

### Local Development
```bash
python tiktok_factcheck.py
```

### Docker
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

Stop bot:
```bash
docker-compose down
```

## Usage

Once the bot is running and added to your Discord server:

1. Send a TikTok, YouTube Short, or Instagram Reel link in the configured channel
2. The bot will automatically:
   - Detect the link
   - Extract video content/title
   - Analyze with Gemini AI
   - Post a fact-check report

3. Type "hello" to get a greeting from the bot

## How It Works

1. **Link Detection**: Bot monitors Discord messages for video URLs
2. **Content Extraction**: 
   - TikTok: Uses oEmbed API + Whisper transcription
   - YouTube: oEmbed + Whisper fallback
   - Instagram: Page scraping + Whisper fallback
3. **AI Analysis**: Sends transcript to Gemini for fact-checking
4. **Results**: Posts detailed fact-check with assessment and sources

## Customization

This bot was specifically coded for personal use. To adapt it:

- Modify `video_patterns` in the code to add more platforms
- Adjust the Gemini prompt in `fact_check_with_gemini()` for different analysis styles
- Change response messages in `process_discord_message()`

## Troubleshooting

**Bot not responding:**
- Check that MESSAGE CONTENT INTENT is enabled in Discord Developer Portal
- Verify bot has permissions to read/send messages in the channel
- Check console logs for errors

**Transcription failing:**
- Ensure yt-dlp and Whisper are installed
- Check temp_downloads directory permissions

**Docker issues:**
- Make sure config file is properly mounted
- Check Docker logs: `docker-compose logs`

## License

Personal use only - created as a custom project.

## Credits

- Built with: Python, aiohttp, Discord API, Google Gemini
- Transcription: OpenAI Whisper, yt-dlp
