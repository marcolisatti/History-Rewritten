# History Rewritten

An automated X (Twitter) bot that generates and posts alternate history events with AI-generated images.

## Overview

History Rewritten creates compelling alternate history scenarios using OpenAI's GPT-4 and DALL-E 3, then automatically posts them to X (Twitter) with accompanying historical-style images. The bot includes uniqueness checking to prevent duplicate content and maintains a log of all generated events.

## Features

- **AI-Generated Events**: Uses GPT-4 to create plausible alternate history scenarios (1850-1990)
- **Historical Images**: Generates period-appropriate images using DALL-E 3
- **Duplicate Prevention**: SHA1 hashing and similarity checking to ensure unique content
- **Twitter Integration**: Automatic posting to X using Twitter API v2
- **Comprehensive Logging**: Detailed logs and JSON history tracking
- **Error Handling**: Robust error handling with retry logic

## Requirements

- Python 3.7+
- OpenAI API key
- Twitter API v2 credentials (API key, secret, access tokens, bearer token)

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your API credentials:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` with your actual API keys

## Configuration

### Required Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `TWITTER_API_KEY`: Twitter API key
- `TWITTER_API_SECRET`: Twitter API secret
- `TWITTER_ACCESS_TOKEN`: Twitter access token
- `TWITTER_ACCESS_TOKEN_SECRET`: Twitter access token secret
- `TWITTER_BEARER_TOKEN`: Twitter bearer token

### Optional Configuration

- `UNIQUENESS_THRESHOLD`: Similarity threshold for duplicate detection (default: 0.7)
- `MAX_RETRIES`: Maximum retries for generating unique events (default: 2)

## Usage

Run the bot:
```bash
python history_rewritten.py
```

The bot will:
1. Generate an alternate history event using GPT-4
2. Check for uniqueness against previous posts
3. Generate a historical-style image using DALL-E 3
4. Post to X (Twitter) with formatted text and image
5. Log the event to `history_log.json`

## Output Files

- `history_log.json`: Complete log of all generated events
- `history_rewritten.log`: Application logs
- `generated_images/`: Directory containing all generated images

## Tweet Format

Posts follow this format:
```
🗓️ [Date]
📍 [Location]

[Event Description]
```

## Error Handling

The bot includes comprehensive error handling for:
- API failures (OpenAI, Twitter)
- Network issues
- Invalid responses
- Duplicate content detection
- File I/O operations

## License

MIT License - see LICENSE file for details.

This project is for educational and entertainment purposes. Ensure compliance with OpenAI and Twitter API terms of service.git