#!/usr/bin/env python3
"""
History Rewritten - Automated X (Twitter) posting of alternate history events
Generates AI-powered historical events and posts them with images to X/Twitter
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
from pathlib import Path

import openai
import tweepy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('history_rewritten.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HistoryRewrittenBot:
    def __init__(self):
        """Initialize the bot with API credentials and configuration"""
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.history_log_file = 'history_log.json'
        self.images_dir = Path('generated_images')
        self.images_dir.mkdir(exist_ok=True)
        
        # Initialize Twitter API v2 client
        self.twitter_client = tweepy.Client(
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
            wait_on_rate_limit=True
        )
        
        # Initialize Twitter API v1.1 for media upload
        auth = tweepy.OAuth1UserHandler(
            os.getenv('TWITTER_API_KEY'),
            os.getenv('TWITTER_API_SECRET'),
            os.getenv('TWITTER_ACCESS_TOKEN'),
            os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        self.twitter_api_v1 = tweepy.API(auth, wait_on_rate_limit=True)

    def generate_event(self) -> Dict[str, str]:
        """Generate an alternate history event using ChatGPT"""
        prompt = """Generate a compelling alternate history event that never actually happened but feels plausible. 

        Requirements:
        - Include a specific date (month, day, year) between 1850-1990
        - Include a specific location (city, country)
        - Create a brief, engaging description suitable for social media
        - Keep the description under 240 characters to leave room for date/location
        - Make it feel historically authentic but clearly fictional
        - Focus on significant but believable alternate outcomes

        Return your response in this exact JSON format:
        {
            "date": "Month DD, YYYY",
            "location": "City, Country",
            "title": "Brief compelling title",
            "description": "Short engaging description under 200 characters",
            "image_prompt": "black and white photographic realism with light grain, slightly aged paper texture, depicting [describe the scene in detail]"
        }

        Examples of good alternate history events:
        - Failed assassination attempts that succeeded
        - Different outcomes of famous meetings
        - Alternate technology developments
        - Different exploration discoveries
        - Alternate political alliances
        """

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            # Remove markdown code block markers if present
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            event_data = json.loads(content)
            
            # Validate required fields
            required_fields = ['date', 'location', 'title', 'description', 'image_prompt']
            if not all(field in event_data for field in required_fields):
                raise ValueError("Missing required fields in generated event")
            
            logger.info(f"Generated event: {event_data['title']}")
            return event_data
            
        except Exception as e:
            logger.error(f"Error generating event: {e}")
            raise

    def load_history_log(self) -> List[Dict]:
        """Load the history log from JSON file"""
        if not os.path.exists(self.history_log_file):
            return []
        
        try:
            with open(self.history_log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading history log: {e}")
            return []

    def save_history_log(self, history_log: List[Dict]):
        """Save the history log to JSON file"""
        try:
            with open(self.history_log_file, 'w', encoding='utf-8') as f:
                json.dump(history_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving history log: {e}")
            raise

    def calculate_content_hash(self, event: Dict[str, str]) -> str:
        """Calculate SHA1 hash of event content for uniqueness checking"""
        content = f"{event['title']}|{event['description']}|{event['location']}"
        return hashlib.sha1(content.encode('utf-8')).hexdigest()

    def check_uniqueness(self, new_event: Dict[str, str], threshold: float = 0.7) -> bool:
        """Check if the new event is unique compared to previous posts"""
        history_log = self.load_history_log()
        new_hash = self.calculate_content_hash(new_event)
        
        # Check for exact hash matches
        for entry in history_log:
            if entry.get('hash') == new_hash:
                logger.info("Event rejected: exact hash match found")
                return False
        
        # Simple similarity check based on title and key words
        new_words = set(new_event['title'].lower().split() + 
                       new_event['description'].lower().split() +
                       new_event['location'].lower().split())
        
        for entry in history_log:
            existing_words = set(entry.get('title', '').lower().split() + 
                               entry.get('description', '').lower().split() +
                               entry.get('location', '').lower().split())
            
            # Calculate Jaccard similarity
            intersection = len(new_words.intersection(existing_words))
            union = len(new_words.union(existing_words))
            similarity = intersection / union if union > 0 else 0
            
            if similarity > threshold:
                logger.info(f"Event rejected: high similarity ({similarity:.2f}) with existing post")
                return False
        
        logger.info("Event passed uniqueness check")
        return True

    def generate_image(self, image_prompt: str, event_title: str) -> str:
        """Generate image using DALL-E and save locally"""
        try:
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            
            # Download and save the image
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            # Create filename from event title
            safe_title = "".join(c for c in event_title if c.isalnum() or c in (' ', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{safe_title}.png"
            filepath = self.images_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(image_response.content)
            
            logger.info(f"Image saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            raise

    def format_post_text(self, event: Dict[str, str]) -> str:
        """Format the event data into a Twitter post with emojis and specific format"""
        # Format: "🗓️ Date\n📍 Location\n\nDescription"
        post_text = f"🗓️ {event['date']}\n📍 {event['location']}\n\n{event['description']}"
        
        # Ensure it's under 280 characters
        if len(post_text) > 280:
            # Truncate description if needed
            header = f"🗓️ {event['date']}\n📍 {event['location']}\n\n"
            available_chars = 280 - len(header) - 3  # 3 for "..."
            truncated_desc = event['description'][:available_chars] + "..."
            post_text = f"{header}{truncated_desc}"
        
        return post_text

    def post_to_x(self, event: Dict[str, str], image_path: str) -> bool:
        """Post the event and image to X (Twitter)"""
        try:
            post_text = self.format_post_text(event)

            # Upload media using API v1.1
            media = self.twitter_api_v1.media_upload(image_path)
            
            # Post tweet using API v2
            response = self.twitter_client.create_tweet(
                text=post_text,
                media_ids=[media.media_id]
            )
            
            if response.data:
                tweet_id = response.data['id']
                logger.info(f"Tweet posted successfully: https://twitter.com/i/web/status/{tweet_id}")
                return True
            else:
                logger.error("Failed to post tweet - no response data")
                return False
                
        except Exception as e:
            logger.error(f"Error posting to X: {e}")
            return False

    def run(self) -> bool:
        """Main execution function"""
        try:
            logger.info("🚀 Starting History Rewritten bot...")
            
            # Generate new event
            logger.info("📝 Generating alternate history event...")
            event = self.generate_event()
            
            # Check uniqueness
            logger.info("🔍 Checking event uniqueness...")
            if not self.check_uniqueness(event):
                logger.info("❌ Event too similar to previous posts, trying again...")
                # Try once more with a new generation
                event = self.generate_event()
                if not self.check_uniqueness(event):
                    logger.error("❌ Unable to generate unique event after 2 attempts")
                    return False
            
            # Generate image
            logger.info("🎨 Generating image...")
            image_path = self.generate_image(event['image_prompt'], event['title'])
            
            # Post to X
            logger.info("📤 Posting to X...")
            if self.post_to_x(event, image_path):
                # Save to history log
                history_log = self.load_history_log()
                event_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'title': event['title'],
                    'date': event['date'],
                    'location': event['location'],
                    'description': event['description'],
                    'image_prompt': event['image_prompt'],
                    'image_path': image_path,
                    'hash': self.calculate_content_hash(event)
                }
                history_log.append(event_entry)
                self.save_history_log(history_log)
                
                logger.info("✅ Post published successfully!")
                return True
            else:
                logger.error("❌ Failed to post to X")
                return False
                
        except Exception as e:
            logger.error(f"❌ Bot execution failed: {e}")
            return False

def main():
    """Main entry point"""
    try:
        # Verify required environment variables
        required_vars = [
            'OPENAI_API_KEY',
            'TWITTER_API_KEY',
            'TWITTER_API_SECRET',
            'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET',
            'TWITTER_BEARER_TOKEN'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
            logger.error("Please check your .env file")
            return False
        
        # Initialize and run bot
        bot = HistoryRewrittenBot()
        return bot.run()
        
    except Exception as e:
        logger.error(f"Application failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)