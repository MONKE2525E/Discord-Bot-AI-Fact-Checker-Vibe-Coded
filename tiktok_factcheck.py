#!/usr/bin/env python3
"""
Discord TikTok Fact Checker - Simple Python Script
Receives Discord webhook messages, transcribes TikToks, fact-checks with Gemini, sends responses
"""

import json
import re
import asyncio
import aiohttp
import aiofiles
from datetime import datetime
from typing import Optional
from aiohttp import web

# Load config
async def load_config():
    async with aiofiles.open('tiktok_factcheck_config.json', 'r') as f:
        return json.loads(await f.read())

class TikTokFactChecker:
    def __init__(self, config):
        self.config = config
        self.session = None

    async def start(self):
        self.session = aiohttp.ClientSession()
        print("🤖 TikTok Fact Checker started")

    async def stop(self):
        if self.session:
            await self.session.close()
        print("🤖 TikTok Fact Checker stopped")

    async def transcribe_tiktok(self, url: str) -> str:
        """Transcribe TikTok - try multiple methods"""
        
        print(f"🔍 Attempting to transcribe: {url}")
        
        # Method 1: Try Playwright to extract TikTok captions (most reliable)
        print("🔄 Trying Playwright browser automation...")
        try:
            transcript = await self._transcribe_with_playwright(url)
            if transcript:
                print(f"✅ Playwright transcription successful!")
                return transcript
        except Exception as e:
            print(f"❌ Playwright failed: {e}")
        
        # Method 2: Try Whisper transcription (download video + transcribe)
        print("🔄 Trying Whisper transcription...")
        try:
            transcript = await self._transcribe_with_whisper(url)
            if transcript:
                print(f"✅ Whisper transcription successful!")
                return transcript
        except Exception as e:
            print(f"❌ Whisper transcription failed: {e}")
        
        # Method 3: Just get TikTok title/description (most reliable fallback)
        print("🔄 Trying TikTok title/description...")
        try:
            async with self.session.get(
                f"https://www.tiktok.com/oembed?url={url}",
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    title = data.get("title", "No title")
                    author = data.get("author_name", "unknown")
                    result = f"TikTok by @{author}: {title}"
                    print(f"✅ Got title/description: {result}")
                    return result
        except Exception as e:
            print(f"❌ TikTok oembed failed: {e}")

        return "Could not retrieve transcript"

    async def _transcribe_with_playwright(self, url: str) -> Optional[str]:
        """Use Playwright to extract TikTok captions"""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # Launch browser (headless)
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Go to TikTok URL
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Wait for page to fully load
                await page.wait_for_timeout(3000)
                
                # Try to find and extract captions/subtitles
                # TikTok stores captions in various places
                
                # Method 1: Look for caption button and click it
                try:
                    caption_button = await page.query_selector('button[aria-label="Captions"]')
                    if caption_button:
                        await caption_button.click()
                        await page.wait_for_timeout(1000)
                except:
                    pass
                
                # Method 2: Look for subtitle/caption text in the page
                caption_text = ""
                
                # Try to find subtitle container
                subtitle_selectors = [
                    '.tiktok-caption',
                    '[class*="caption"]',
                    '[class*="subtitle"]',
                    '.captions-display',
                ]
                
                for selector in subtitle_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            caption_text = await element.inner_text()
                            if caption_text and len(caption_text) > 20:
                                break
                    except:
                        continue
                
                # Method 3: Get the video description (often contains what was said)
                if not caption_text or len(caption_text) < 20:
                    try:
                        desc_element = await page.query_selector('[data-e2e="video-description"]')
                        if desc_element:
                            caption_text = await desc_element.inner_text()
                    except:
                        pass
                
                await browser.close()
                
                if caption_text and len(caption_text) > 20:
                    return caption_text
                
                return None
                
        except ImportError:
            print("⚠️ Playwright not installed")
            return None
        except Exception as e:
            print(f"❌ Playwright error: {e}")
            return None

    async def _extract_transcript_with_gemini(self, html: str, url: str) -> Optional[str]:
        """Use Gemini to extract transcript from raw HTML"""
        
        prompt = f"""
You are given the raw HTML from a TikTok video page. Your task is to extract and reconstruct the spoken content from the video.

Look for:
1. Any caption/subtitle data in script tags (often JSON with "caption", "text", "subtitles" keys)
2. Any description text that describes what happens in the video
3. Any text that appears to be the actual spoken words

Ignore:
- HTML markup, CSS, JavaScript code
- UI elements, buttons, navigation
- Metadata, timestamps, video IDs
- Hashtags and mentions (unless they describe the content)

Return ONLY the actual spoken content/transcript of what the person says in the video. If you cannot find any spoken content, say "NO_TRANSCRIPT_FOUND".

TikTok URL: {url}

Raw HTML (first 15000 chars):
{html[:15000]}
"""

        try:
            headers = {"Content-Type": "application/json"}
            
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 2000
                }
            }
            
            async with self.session.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.config['gemini_api_key']}",
                json=data,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    
                    if content and "NO_TRANSCRIPT_FOUND" not in content and len(content) > 20:
                        return content
                    else:
                        print(f"⚠️ Gemini couldn't find transcript in HTML")
                        return None
                else:
                    print(f"❌ Gemini extraction failed: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Gemini extraction error: {e}")
            return None

    async def _transcribe_with_whisper(self, url: str) -> Optional[str]:
        """Download TikTok video and transcribe with Whisper"""
        try:
            import subprocess
            import os
            
            # Create temp directory
            temp_dir = "temp_downloads"
            os.makedirs(temp_dir, exist_ok=True)
            output_file = os.path.join(temp_dir, "tiktok_video.mp4")
            
            # Use yt-dlp to download TikTok video
            print(f"📥 Downloading TikTok video...")
            result = subprocess.run(
                ["yt-dlp", "-f", "best", "-o", output_file, url],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0 or not os.path.exists(output_file):
                print(f"❌ Download failed: {result.stderr}")
                return None
            
            print(f"📥 Video downloaded, transcribing with Whisper...")
            
            # Use whisper CLI to transcribe
            result = subprocess.run(
                ["whisper", "--model", "tiny", "--language", "en", "--output_format", "txt", output_file],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Read the transcript
            transcript_file = output_file.replace(".mp4", ".txt")
            if os.path.exists(transcript_file):
                with open(transcript_file, 'r') as f:
                    transcript = f.read()
                
                # Cleanup
                try:
                    os.remove(output_file)
                    os.remove(transcript_file)
                except:
                    pass
                
                if transcript and len(transcript) > 10:
                    return transcript
            
            print(f"❌ Whisper transcription failed")
            return None
            
        except FileNotFoundError:
            print(f"⚠️ yt-dlp or whisper not installed")
            return None
        except Exception as e:
            print(f"❌ Whisper error: {e}")
            return None

    async def fact_check_with_gemini(self, transcript: str) -> str:
        """Fact check transcript using Gemini API"""
        
        prompt = f"""
Please fact check this TikTok transcript. Analyze the claims made and provide:
1. A fact-check assessment (TRUE, FALSE, MISLEADING, etc.)
2. Brief explanation with sources if possible
3. Confidence level

Transcript to fact check:
"{transcript}"

Please be concise and focus on factual accuracy.
"""

        try:
            headers = {
                "Content-Type": "application/json",
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            async with self.session.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.config['gemini_api_key']}",
                json=data,
                headers=headers,
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    print(f"✅ Got fact check from Gemini")
                    return content
                else:
                    error_text = await response.text()
                    print(f"❌ Gemini API error: {response.status} - {error_text}")
                    return "Gemini API error"
        except Exception as e:
            print(f"❌ Gemini request failed: {e}")
            return "Gemini request failed"

    async def send_discord_message(self, message: str, embed: dict = None):
        """Send message to Discord webhook"""
        
        payload = {"content": message}
        if embed:
            payload["embeds"] = [embed]

        try:
            async with self.session.post(
                self.config["discord_webhook"],
                json=payload,
                timeout=15
            ) as response:
                if response.status in [204, 200]:
                    print(f"✅ Message sent to Discord")
                else:
                    error_text = await response.text()
                    print(f"❌ Discord webhook error: {response.status} - {error_text}")
        except Exception as e:
            print(f"❌ Discord send failed: {e}")

    async def process_discord_message(self, message_data: dict):
        """Process Discord message with video link"""
        content = message_data.get("content", "")
        author = message_data.get("author", {}).get("username", "Unknown")
        video_type = message_data.get("video_type", "tiktok")
        video_url = message_data.get("video_url")
        
        if not video_url:
            # Extract URL from content for backward compatibility
            tiktok_urls = re.findall(r'https?://(?:www\.)?tiktok\.com/[^\s]+', content)
            if tiktok_urls:
                video_url = tiktok_urls[0]
                video_type = "tiktok"
            else:
                return
        
        print(f"🤖 Processing {video_type.upper()} from {author}... This may take a moment.")
        
        # Send processing message
        try:
            await self.send_discord_message(f"🤖 Processing {video_type.replace('_', ' ').title()} from {author}... This may take a moment.")
        except:
            pass
        
        # Get video info based on type
        if video_type == "tiktok":
            transcript = await self.transcribe_tiktok(video_url)
        elif video_type == "youtube_shorts":
            transcript = await self.transcribe_youtube_shorts(video_url)
        elif video_type == "instagram_reels":
            transcript = await self.transcribe_instagram_reels(video_url)
        else:
            transcript = "Could not retrieve transcript"
        
        # Ensure transcript is not None
        if transcript is None:
            transcript = "Could not retrieve transcript"
        
        print(f"📝 Transcript: {transcript[:100]}...")
        
        # Fact check
        fact_check = await self.fact_check_with_gemini(transcript)
        print(f"🔍 Fact check: {fact_check[:100]}...")
        
        # Create embed
        embed = {
            "title": f"🔍 {video_type.replace('_', ' ').title()} Fact Check Results",
            "color": 3447003,
            "fields": [
                {
                    "name": "👤 Original Poster",
                    "value": author,
                    "inline": True
                },
                {
                    "name": f"🎵 {video_type.replace('_', ' ').title()} URL",
                    "value": video_url,
                    "inline": True
                },
                {
                    "name": "📝 Transcript",
                    "value": transcript[:500] + "..." if len(transcript) > 500 else transcript,
                    "inline": False
                },
                {
                    "name": "🔍 Fact Check",
                    "value": fact_check[:1000] + "..." if len(fact_check) > 1000 else fact_check,
                    "inline": False
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_discord_message(
            f"✅ Fact check complete for {author}'s {video_type.replace('_', ' ').title()}:",
            embed=embed
        )

    async def transcribe_youtube_shorts(self, url: str) -> str:
        """Transcribe YouTube Shorts video"""
        try:
            # First try to get title/description from oEmbed
            try:
                video_id = None
                if '/shorts/' in url:
                    video_id = url.split('/shorts/')[1].split('?')[0].split('&')[0]
                elif 'youtu.be/' in url:
                    video_id = url.split('youtu.be/')[1].split('?')[0].split('&')[0]
                
                if video_id:
                    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
                    async with self.session.get(oembed_url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            title = data.get("title", "No title")
                            author = data.get("author_name", "Unknown")
                            return f"YouTube Shorts by @{author}: {title}"
            except Exception as e:
                print(f"⚠️ YouTube oEmbed failed: {e}")
            
            # Fallback: try to download and transcribe
            import subprocess
            import os
            
            # Create temp directory
            temp_dir = "temp_downloads"
            os.makedirs(temp_dir, exist_ok=True)
            output_file = os.path.join(temp_dir, "youtube_shorts_video.mp4")
            
            # Use yt-dlp to download YouTube Shorts video
            print(f"📥 Downloading YouTube Shorts video...")
            result = subprocess.run(
                ["yt-dlp", "-f", "best", "-o", output_file, url],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0 or not os.path.exists(output_file):
                print(f"❌ Download failed: {result.stderr}")
                return "Could not download YouTube Shorts"
            
            print(f"📥 Video downloaded, transcribing with Whisper...")
            
            # Use whisper CLI to transcribe
            result = subprocess.run(
                ["whisper", "--model", "tiny", "--language", "en", "--output_format", "txt", output_file],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Read the transcript
            transcript_file = output_file.replace(".mp4", ".txt")
            if os.path.exists(transcript_file):
                with open(transcript_file, 'r') as f:
                    transcript = f.read()
                
                # Cleanup
                try:
                    os.remove(output_file)
                    os.remove(transcript_file)
                except:
                    pass
                
                if transcript and len(transcript) > 10:
                    return transcript
            
            print(f"❌ Whisper transcription failed")
            return "Could not transcribe YouTube Shorts"
            
        except FileNotFoundError:
            print(f"⚠️ yt-dlp or whisper not installed")
            return "Transcription tools not available"
        except Exception as e:
            print(f"❌ YouTube Shorts error: {e}")
            return f"Error processing YouTube Shorts: {str(e)[:100]}"

    async def transcribe_instagram_reels(self, url: str) -> str:
        """Transcribe Instagram Reels video"""
        try:
            # Instagram is more restrictive, try to get basic info from page
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                }
                async with self.session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        # Try to extract title/description from meta tags
                        import re
                        title_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]*)"', html)
                        desc_match = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]*)"', html)
                        
                        title = title_match.group(1) if title_match else "No title"
                        desc = desc_match.group(1) if desc_match else "No description"
                        
                        if title or desc:
                            return f"Instagram Reel: {title} - {desc}"
            except Exception as e:
                print(f"⚠️ Instagram page fetch failed: {e}")
            
            # Fallback: try to download and transcribe
            import subprocess
            import os
            
            # Create temp directory
            temp_dir = "temp_downloads"
            os.makedirs(temp_dir, exist_ok=True)
            output_file = os.path.join(temp_dir, "instagram_reels_video.mp4")
            
            # Use yt-dlp to download Instagram Reels video
            print(f"📥 Downloading Instagram Reels video...")
            result = subprocess.run(
                ["yt-dlp", "-f", "best", "-o", output_file, url],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0 or not os.path.exists(output_file):
                print(f"❌ Download failed: {result.stderr}")
                return "Could not download Instagram Reel"
            
            print(f"📥 Video downloaded, transcribing with Whisper...")
            
            # Use whisper CLI to transcribe
            result = subprocess.run(
                ["whisper", "--model", "tiny", "--language", "en", "--output_format", "txt", output_file],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Read the transcript
            transcript_file = output_file.replace(".mp4", ".txt")
            if os.path.exists(transcript_file):
                with open(transcript_file, 'r') as f:
                    transcript = f.read()
                
                # Cleanup
                try:
                    os.remove(output_file)
                    os.remove(transcript_file)
                except:
                    pass
                
                if transcript and len(transcript) > 10:
                    return transcript
            
            print(f"❌ Whisper transcription failed")
            return "Could not transcribe Instagram Reel"
            
        except FileNotFoundError:
            print(f"⚠️ yt-dlp or whisper not installed")
            return "Transcription tools not available"
        except Exception as e:
            print(f"❌ Instagram Reels error: {e}")
            return f"Error processing Instagram Reel: {str(e)[:100]}"

    async def send_discord_message(self, message: str, embed: dict = None):
        """Send message to Discord webhook"""
        
        payload = {"content": message}
        if embed:
            payload["embeds"] = [embed]

        try:
            async with self.session.post(
                self.config["discord_webhook"],
                json=payload,
                timeout=15
            ) as response:
                if response.status in [204, 200]:
                    print(f"✅ Message sent to Discord")
                else:
                    error_text = await response.text()
                    print(f"❌ Discord webhook error: {response.status} - {error_text}")
        except Exception as e:
            print(f"❌ Discord send failed: {e}")

# Web server setup
async def handle_webhook(request):
    """Handle Discord webhook requests"""
    try:
        message_data = await request.json()
        print(f"📥 Received webhook: {json.dumps(message_data, indent=2)}")
        
        # Process the message
        await request.app['checker'].process_discord_message(message_data)
        
        return web.json_response({"status": "ok"})
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_health(request):
    """Health check endpoint"""
    return web.json_response({"status": "running"})

async def main():
    config = await load_config()
    checker = TikTokFactChecker(config)
    
    await checker.start()
    
    # Check if we have bot token for polling
    if config.get("discord_bot_token") and config.get("discord_channel_id"):
        print("🔄 Using Discord bot with real-time message events")
        
        # Start background polling task
        async def poll_discord():
            processed_messages = set()  # Track processed message IDs
            ready_printed = False  # Only print ready once
            
            # Connect to Discord gateway
            gateway_url = None
            try:
                # Get gateway URL
                async with checker.session.get(
                    "https://discord.com/api/v10/gateway/bot",
                    headers={"Authorization": f"Bot {config['discord_bot_token']}"},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        gateway_data = await response.json()
                        gateway_url = gateway_data.get("url")
                        print(f"🔌 Connecting to Discord gateway: {gateway_url}")
            except Exception as e:
                print(f"❌ Could not get gateway URL: {e}")
                return
            
            # WebSocket connection
            import websockets
            
            while True:
                try:
                    async with websockets.connect(f"{gateway_url}?v=10&encoding=json") as ws:
                        # Identify to gateway with proper intents
                        identify_payload = {
                            "op": 2,
                            "d": {
                                "token": config['discord_bot_token'],
                                "intents": 33280,  # GUILDS + GUILD_MESSAGES + MESSAGE_CONTENT
                                "properties": {
                                    "os": "linux",
                                    "browser": "tiktok-fact-checker",
                                    "device": "tiktok-fact-checker"
                                }
                            }
                        }
                        await ws.send(json.dumps(identify_payload))
                        print("✅ Connected to Discord gateway")
                        
                        # Handle gateway events
                        async for message in ws:
                            data = json.loads(message)
                            if data.get("op") == 10:  # Hello - heartbeat
                                heartbeat_interval = data["d"]["heartbeat_interval"] / 1000
                                asyncio.create_task(heartbeat_loop(ws, heartbeat_interval))
                            elif data.get("op") == 0 and not ready_printed:  # Ready
                                print("✅ Bot is online and ready!")
                                ready_printed = True
                                # Send startup message only once
                                try:
                                    await checker.send_discord_message("🤖 TikTok Fact Check Bot is now online! Send me a TikTok link and I'll fact-check it for you! 🔍")
                                    print("📢 Sent startup message to Discord")
                                except Exception as e:
                                    print(f"⚠️ Could not send startup message: {e}")
                            elif data.get("t") == "MESSAGE_CREATE":  # New message
                                await process_message(data.get("d", {}), checker, config, processed_messages)
                                
                except Exception as e:
                    print(f"❌ Gateway error: {e}")
                    ready_printed = False
                    await asyncio.sleep(5)
        
        async def process_message(msg_data, checker, config, processed_messages):
            try:
                msg_id = msg_data.get("id")
                channel_id = msg_data.get("channel_id")
                
                # Skip if not our channel or already processed
                if channel_id != config['discord_channel_id'] or msg_id in processed_messages:
                    return
                
                content = msg_data.get("content", "")
                author = msg_data.get("author", {}).get("username", "Unknown")
                author_id = msg_data.get("author", {}).get("id", "")
                is_bot = msg_data.get("author", {}).get("bot", False)
                
                # Print FULL message content for debugging
                print(f"\n{'='*60}")
                print(f"📨 NEW MESSAGE from {author} (ID: {author_id}) at {datetime.now().strftime('%H:%M:%S')}")
                print(f"Is bot: {is_bot}")
                print(f"Content: {content}")
                print(f"{'='*60}\n")
                
                processed_messages.add(msg_id)
                
                # IGNORE ALL BOT MESSAGES (including our own)
                if is_bot:
                    print("🤖 Ignoring bot message")
                    return
                
                # Check for video URLs (TikTok, YouTube Shorts, Instagram Reels)
                video_patterns = {
                    'tiktok': [
                        r'https?://(?:www\.)?tiktok\.com/[^\s]+',
                        r'https?://(?:vm\.)?tiktok\.com/[^\s]+',
                        r'https?://(?:m\.)?tiktok\.com/[^\s]+',
                    ],
                    'youtube_shorts': [
                        r'https?://(?:www\.)?youtube\.com/shorts/[^\s]+',
                        r'https?://(?:www\.)?youtu\.be/[^\s]+',
                        r'https?://youtube\.com/shorts/[^\s]+',
                    ],
                    'instagram_reels': [
                        r'https?://(?:www\.)?instagram\.com/reel/[^\s]+',
                        r'https?://(?:www\.)?instagram\.com/reels/[^\s]+',
                        r'https?://instagram\.com/reel/[^\s]+',
                    ]
                }
                
                found_video = False
                video_type = None
                video_url = None
                
                for platform, patterns in video_patterns.items():
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            video_url = matches[0]
                            video_type = platform
                            found_video = True
                            print(f"🎵 {platform.upper()} URL FOUND: {video_url}")
                            break
                    if found_video:
                        break
                
                if found_video:
                    # Process the video
                    msg_data = {
                        "content": content,
                        "author": {"username": author},
                        "video_type": video_type,
                        "video_url": video_url
                    }
                    await checker.process_discord_message(msg_data)
                else:
                    print(f"❌ No video URL found in message")
                    # If message says "hello" or similar, respond
                    if any(word in content.lower() for word in ['hello', 'hi', 'hey']):
                        print(f"👋 Responding to greeting from {author}")
                        try:
                            await checker.send_discord_message(f"Hello {author}! 👋 I'm ready to fact-check TikToks, YouTube Shorts, and Instagram Reels! Just send me a link and I'll analyze it for you! 🔍")
                            print(f"✅ Sent hello response to {author}")
                        except Exception as e:
                            print(f"❌ Could not send hello: {e}")
                
                # Keep processed set manageable
                if len(processed_messages) > 100:
                    processed_messages = set(list(processed_messages)[-50:])
                    
            except Exception as e:
                print(f"❌ Message processing error: {e}")
                import traceback
                traceback.print_exc()
        
        async def heartbeat_loop(ws, interval):
            while True:
                try:
                    await ws.send(json.dumps({"op": 1, "d": None}))
                    await asyncio.sleep(interval)
                except:
                    break
        
        # Start polling in background
        poll_task = asyncio.create_task(poll_discord())
    
    # Also start web server for webhook (optional)
    app = web.Application()
    app['checker'] = checker
    
    app.router.add_post('/webhook', handle_webhook)
    app.router.add_get('/health', handle_health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    print("🚀 TikTok Fact Checker is running!")
    print("📡 Webhook endpoint: http://localhost:8080/webhook")
    print("📡 Health check: http://localhost:8080/health")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        await runner.cleanup()
        await checker.stop()

if __name__ == "__main__":
    asyncio.run(main())
