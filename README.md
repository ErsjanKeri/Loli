# 🎓 Loli Video Generator

# PLEASE WATCH THE generated_videos THEY ARE AWESOME! 

An advanced educational video generation platform powered by multiple AI models including AWS Bedrock and OpenAI.

## ✨ Features

- **Multi-Model AI Pipeline**: 4-stage AI processing with user-selected models for explanation, GPT-5 refinement, and Claude-4 script generation
- **AWS Bedrock Integration**: Access to Claude, Llama, Titan, and other foundation models
- **OpenAI ChatGPT-5**: Premium AI model integration for text refinement
- **AWS Polly Voiceover**: Neural voice synthesis with multiple voice options
- **S3 Cloud Storage**: Automatic video upload to AWS S3 with public URLs
- **Educational Video Generation**: Renders mathematical animations using Manim
- **RESTful API**: Clean REST endpoints with enhanced metadata
- **Real-time Progress Tracking**: Detailed status updates through multi-stage processing
- **Voice Selection**: Choose from multiple AWS Polly neural voices
- **Docker Support**: Easy deployment with Docker and Docker Compose

## 🏗️ Project Structure

```
loli/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app setup
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py            # API endpoints
│   │   └── dependencies.py      # Dependency injection
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration settings
│   │   └── exceptions.py        # Custom exceptions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_orchestrator.py   # Multi-model AI coordination
│   │   ├── aws_bedrock.py       # AWS Bedrock service
│   │   ├── openai_service.py    # OpenAI ChatGPT-5 integration
│   │   ├── aws_polly.py         # AWS Polly TTS service
│   │   ├── script_generator.py  # Legacy script generation (Gemini)
│   │   ├── video_processor.py   # Manim video processing
│   │   └── storage.py           # Video storage management
│   └── models/
│       ├── __init__.py
│       └── video.py             # Pydantic models
├── generated_videos/            # Local video storage
├── media/voiceovers/           # Voice cache directory
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env                        # Environment configuration
├── TECHNICAL_SPECS.md          # Detailed technical specifications
└── README.md
```


## 🔧 Prerequisites

- **Python 3.10+**
- **FFmpeg** (for video processing)
- **LaTeX** (for mathematical expressions)
- **AWS Account** with:
  - AWS Bedrock access (Claude, Llama models)
  - AWS Polly access
  - S3 bucket permissions
- **OpenAI API Key** (for ChatGPT-5)

## 🚀 Multi-Stage AI Processing Pipeline

The system uses a sophisticated 5-stage AI processing pipeline:

1. **Initial Explanation** - User-selected model (Claude-3.5-Sonnet, Claude-4, etc.)
2. **GPT-5 Refinement** - Improves clarity, fixes logic, updates deprecated info
3. **Claude-4 Script Generation** - Converts explanation to Manim script
4. **Claude-4 Script Validation** - Validates and fixes script issues
5. **Claude-4 Visual Validation** - Optimizes visual composition and element positioning

## 🛠️ Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd loli
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   cd app
   pip install -r requirements.txt
   pip install manim
   ```

4. **Set up environment variables**
   ```bash
   # Edit app/.env with your API keys and AWS credentials
   nano app/.env
   ```
   
   Required environment variables:
   ```bash
   # AWS Configuration
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_REGION=eu-west-3
   S3_BUCKET_NAME=loli
   
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   
   # API Settings
   API_HOST=0.0.0.0
   API_PORT=8000
   LOG_LEVEL=DEBUG
   ```

5. **Run the application**
   ```bash
   # From project root directory
   PYTHONPATH=/path/to/loli uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker Deployment

1. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

## 📡 API Endpoints

### Configuration

- `GET /api/v1/config` - Get available models and voices

### Video Management

- `POST /api/v1/videos` - Create a new video generation request with model and voice selection
- `GET /api/v1/videos/{video_id}/status` - Check video generation status with S3 URL
- `GET /api/v1/videos/{video_id}/download` - Download completed video (legacy support)
- `GET /api/v1/videos/{video_id}/script` - Get the generated Manim script
- `DELETE /api/v1/videos/{video_id}` - Delete video and files
- `GET /api/v1/videos` - List all videos (with optional status filter)

### System Management

- `GET /api/v1/health` - System health check
- `GET /api/v1/stats` - API usage statistics
- `POST /api/v1/cleanup` - Manually trigger cleanup of old videos

### 📋 Example Usage

**Get available models and voices:**
```bash
curl "http://localhost:8000/api/v1/config"
```

Response:
```json
{
  "models": ["claude-3-5-sonnet", "claude-3-7-sonnet", "claude-4-sonnet", "claude-3-sonnet", "claude-3-haiku"],
  "voices": ["Joanna", "Matthew", "Ruth", "Stephen"]
}
```

**Create a video with model and voice selection:**
```bash
curl -X POST "http://localhost:8000/api/v1/videos" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain the Pythagorean theorem with visual proof",
    "model": "claude-4-sonnet",
    "voice": "Joanna"
  }'
```

**Check status (completed):**
```bash
curl "http://localhost:8000/api/v1/videos/{video_id}/status"
```

Response:
```json
{
  "video_id": "uuid",
  "status": "completed",
  "message": "Video generated successfully",
  "s3_url": "https://loli.s3.eu-west-3.amazonaws.com/{video_id}.mp4",
  "progress": 100,
  "original_question": "Explain the Pythagorean theorem with visual proof",
  "initial_explanation": "The Pythagorean theorem states...",
  "refined_explanation": "The Pythagorean theorem is a fundamental..."
}
```

## ⚙️ Configuration

All configuration is managed through environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | 0.0.0.0 | Host to bind the API |
| `API_PORT` | 8000 | Port to run the API |
| `LOG_LEVEL` | DEBUG | Logging level |
| `AWS_ACCESS_KEY_ID` | - | AWS access key for Bedrock, Polly, S3 |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key |
| `AWS_REGION` | eu-west-3 | AWS region |
| `S3_BUCKET_NAME` | loli | S3 bucket for video storage |
| `OPENAI_API_KEY` | - | OpenAI API key for ChatGPT-5 |
| `VIDEOS_DIR` | generated_videos | Local directory for temp video storage |
| `TEMP_DIR` | /tmp/manim_videos | Temporary directory for processing |
| `MAX_CONCURRENT_VIDEOS` | 2 | Maximum concurrent video generations |
| `VIDEO_RETENTION_DAYS` | 7 | Days to keep videos before cleanup |

## 🏗️ Architecture

### Multi-Model AI Services

- **AIOrchestrator**: Coordinates the 4-stage AI processing pipeline
- **BedrockService**: Handles AWS Bedrock model interactions (Claude, Llama, Titan)
- **OpenAIService**: Manages ChatGPT-5 integration for text refinement
- **PollyService**: AWS Polly text-to-speech integration

### Core Services

- **VideoProcessor**: Manages Manim execution and video rendering
- **VideoStorage**: Manages video lifecycle and metadata
- **S3VideoService**: Handles video upload to AWS S3 with metadata

### Enhanced Models

- **VideoRequest**: Input validation with model and voice selection
- **VideoResponse**: API response with S3 URLs and AI processing metadata
- **VideoInfo**: Internal video metadata with multi-stage processing data

### Processing Stages

1. **QUEUED** → **GENERATING_INITIAL_EXPLANATION** → **REFINING_EXPLANATION** 
2. **GENERATING_SCRIPT** → **VALIDATING_SCRIPT** → **VISUAL_VALIDATION**
3. **RENDERING_VIDEO** → **UPLOADING_TO_S3** → **COMPLETED**

### Features

- **Multi-Model AI Pipeline**: 5-stage processing with different AI models
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Real-time Progress**: Detailed status tracking through all stages
- **Cloud Storage**: S3 integration with public URLs and metadata
- **Voice Selection**: Multiple AWS Polly neural voices
- **Logging**: Structured logging throughout the application
- **Validation**: Input validation using Pydantic
- **Background Tasks**: Async video processing
- **Resource Management**: Automatic cleanup and limits

## 🛠️ Development

### Adding New AI Models

The modular architecture makes it easy to extend:

1. **New AI Service**: Create in `app/services/` (e.g., `gemini_service.py`)
2. **Update AIOrchestrator**: Add model routing in `app/services/ai_orchestrator.py`
3. **Configuration**: Update model lists in `app/core/config.py`
4. **API**: Update available models in `app/api/routes.py`

### Adding New Features

1. **New endpoints**: Add to `app/api/routes.py`
2. **New services**: Create in `app/services/`
3. **New models**: Add to `app/models/`
4. **Configuration**: Update `app/core/config.py`

### Adding New Voice Providers

1. **New TTS Service**: Implement `SpeechService` interface
2. **Voice Selection**: Update available voices in configuration
3. **Integration**: Add to video processing pipeline

### AWS Services Integration

- **Bedrock Models**: Update model IDs in `BedrockService`
- **S3 Configuration**: Modify bucket settings and permissions
- **Polly Voices**: Add new neural voices to configuration

## 📊 Monitoring

### Health Checks

- `GET /api/v1/health` provides system status
- Docker health checks included
- Monitors Manim and FFmpeg availability
- AWS service connectivity checks

### Logging

- Structured logging with timestamps
- Multi-stage processing tracking
- AI model performance metrics
- S3 upload status and errors
- Error tracking and debugging info
- Configurable log levels

### Metrics

- Video generation success/failure rates
- Processing time per stage
- AI model usage statistics
- S3 storage usage
- Voice synthesis performance

---

For detailed technical specifications and implementation details, see [TECHNICAL_SPECS.md](TECHNICAL_SPECS.md).
