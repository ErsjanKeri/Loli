# 🔧 Technical Specifications & Implementation Guide

## 🏗️ Architecture Overview

### **Updated Multi-Model Educational Video Generation Architecture**

#### **🚀 NEW: Multi-Stage AI Processing with S3 Storage**

#### Previous Architecture (Deprecated)
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Google Gemini  │    │   Azure TTS     │
│   Backend       │────│   2.5-pro        │────│   Services      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Local File    │    │      Manim       │    │   Docker        │
│   Storage       │    │   Video Engine   │    │   Container     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

#### New Multi-Stage AI Processing Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React         │    │   FastAPI        │    │ User Selected   │
│   Frontend      │────│   Orchestrator   │────│ Model (Step 1)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────┐
         │                       │              │ Initial         │
         │                       │              │ Explanation     │
         │                       │              └─────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────┐
         │                       │              │   GPT-5         │
         │                       │              │ Refinement      │
         │                       │              └─────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────┐
         │                       │              │  Claude-4       │
         │                       │              │ Manim Script    │
         │                       │              └─────────────────┘
         │                       │                       │
         │                       │                       ▼
         │                       │              ┌─────────────────┐
         │                       │              │  Claude-4       │
         │                       │              │Script Validation│
         │                       │              └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │   Local Manim   │    │   AWS Polly     │
         │              │   Processing    │────│   Voiceover     │
         │              └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │  Local Video    │◄─────────────┘
         │              │  Generation     │
         │              └─────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         │              │   S3 Upload     │
         │              │  "loli" bucket  │
         │              └─────────────────┘
         │                       │
         │                       ▼
         └──────────────► ┌─────────────────┐
                         │  Public S3 URL  │
                         │   Response      │
                         └─────────────────┘
```

**Complete Flow Explanation:**
1. **Frontend Request**: React sends video request with user-selected model and voice
2. **Step 1 - Initial Explanation**: User-selected model generates initial explanation
3. **Step 2 - GPT-5 Refinement**: GPT-5 refines explanation for clarity, accuracy, and intuitiveness
4. **Step 3 - Claude-4 Script Generation**: Claude-4 converts refined explanation to Manim script
5. **Step 4 - Claude-4 Script Validation**: Claude-4 validates and fixes the generated script
6. **Step 5 - Local Video Processing**: Manim processes script with AWS Polly voiceover (using Step 1 text)
7. **Step 6 - S3 Upload**: Video uploaded to "loli" S3 bucket with metadata
8. **Step 7 - Response**: API returns public S3 URL with video metadata

## 📦 Technical Specifications

### 1. Multi-Stage AI Processing Pipeline

#### Purpose and Goals
Implement a sophisticated 4-stage AI processing pipeline that ensures high-quality educational content through multiple model interactions, culminating in Claude-4 generated Manim scripts.

#### Stage 1: Initial Explanation Generation
- **Input**: User question + selected model
- **Process**: User-selected model generates initial educational explanation
- **Models Available**: All current Bedrock models (claude-3-5-sonnet, claude-3-7-sonnet, claude-4-sonnet, etc.)
- **Output**: Raw educational explanation text

#### Stage 2: GPT-5 Refinement
- **Input**: Initial explanation from Stage 1
- **Process**: GPT-5 refines explanation for:
  - **Clarity improvement**: Make concepts easier to understand
  - **Logical error correction**: Fix any logical inconsistencies
  - **Deprecated information updates**: Ensure accuracy and currency
  - **Intuitive connections**: Better flow and conceptual linking
- **Output**: Refined, high-quality explanation text

#### Stage 3: Claude-4 Manim Script Generation
- **Input**: Refined explanation from Stage 2
- **Process**: Claude-4 Sonnet converts explanation to executable Manim script
- **Requirements**: 
  - Visual representation of concepts
  - Mathematical accuracy
  - Clear animation sequences
- **Output**: Manim Python script

#### Stage 4: Claude-4 Script Validation
- **Input**: Generated Manim script from Stage 3
- **Process**: Claude-4 Sonnet validates and fixes script issues
- **Validation Areas**:
  - Syntax correctness
  - Manim API compatibility
  - Visual flow optimization
- **Output**: Final validated Manim script

### 2. Enhanced Video Processing with S3 Integration

#### Purpose and Goals
Replace local video storage with AWS S3 integration while maintaining local Manim processing for reliability and performance.

#### Local Processing Requirements
- **Manim Rendering**: Keep current local Manim processing (proven working)
- **AWS Polly Integration**: Use selected voice for voiceover generation
- **Voiceover Text Source**: Use **Stage 1 initial explanation** as voiceover narration
- **Temporary Storage**: Use local temp directories for processing

#### S3 Upload Requirements
- **Bucket Name**: "loli" (fixed bucket name)
- **File Naming**: `{video_id}.mp4` (consistent with current system)
- **Upload Process**: After local video generation, upload to S3
- **Permissions**: Public read access for direct URL sharing
- **Metadata Storage**: Include original question and explanation as S3 object metadata

#### Video Response Updates
- **Return Format**: Public S3 URL instead of local file path
- **URL Format**: `https://loli.s3.{region}.amazonaws.com/{video_id}.mp4`
- **Metadata Inclusion**: Original question and refined explanation in response

### 3. Enhanced Status Tracking System

#### Purpose and Goals
Provide detailed progress tracking through the multi-stage AI processing pipeline.

#### New Status Enumeration
```python
class VideoStatus(str, Enum):
    QUEUED = "queued"
    GENERATING_INITIAL_EXPLANATION = "generating_initial_explanation"
    REFINING_EXPLANATION = "refining_explanation" 
    GENERATING_SCRIPT = "generating_script"
    VALIDATING_SCRIPT = "validating_script"
    RENDERING_VIDEO = "rendering_video"
    UPLOADING_TO_S3 = "uploading_to_s3"
    COMPLETED = "completed"
    FAILED = "failed"
```

#### Progress Tracking
- **Stage 1**: 0-20% (Initial explanation)
- **Stage 2**: 20-40% (GPT-5 refinement)
- **Stage 3**: 40-60% (Claude-4 script generation)
- **Stage 4**: 60-70% (Claude-4 script validation)
- **Stage 5**: 70-90% (Local video rendering)
- **Stage 6**: 90-95% (S3 upload)
- **Stage 7**: 100% (Completed)

### 4. New API Endpoints

#### Single Configuration Endpoint
```
GET /api/v1/config
```

**Response Format:**
```json
{
  "models": [
    "claude-4-sonnet",
  ],
  "voices": [
    "Joanna",
    "Matthew", 
    "Ruth",
    "Stephen"
  ]
}
```

#### Updated Video Creation Endpoint
```
POST /api/v1/videos
```

**Request Format:**
```json
{
  "prompt": "Explain the Pythagorean theorem with visual proof",
  "model": "claude-4-sonnet",
  "voice": "Joanna"
}
```

**Response Format:**
```json
{
  "video_id": "uuid",
  "status": "queued",
  "message": "Video generation started", 
  "video_url": null,
  "s3_url": null,
  "created_at": "timestamp",
  "progress": 0,
  "original_question": "Explain the Pythagorean theorem with visual proof",
  "initial_explanation": null,
  "refined_explanation": null
}
```

#### Enhanced Status Endpoint
```
GET /api/v1/videos/{video_id}/status
```

**Response Format (Completed):**
```json
{
  "video_id": "uuid",
  "status": "completed",
  "message": "Video generated successfully",
  "video_url": null,
  "s3_url": "https://loli.s3.eu-west-3.amazonaws.com/{video_id}.mp4",
  "created_at": "timestamp", 
  "progress": 100,
  "original_question": "Explain the Pythagorean theorem with visual proof",
  "initial_explanation": "The Pythagorean theorem states...",
  "refined_explanation": "The Pythagorean theorem is a fundamental..."
}
```

### 5. AWS Services Integration

#### S3 Bucket Configuration
- **Bucket Name**: "loli"
- **Region**: eu-west-3 (consistent with current setup)
- **Access**: Public read for generated videos
- **CORS**: Enabled for web frontend access
- **Versioning**: Disabled (not needed for demo)
- **Lifecycle**: No automatic deletion (cluttered bucket acceptable)

#### S3 Object Metadata
```json
{
  "original-question": "User's original question",
  "initial-explanation": "Stage 1 explanation text",
  "refined-explanation": "Stage 2 refined text",
  "model-used": "claude-4-sonnet",
  "voice-used": "Joanna",
  "generation-date": "timestamp"
}
```

#### AWS Polly Voice Configuration
- **Available Voices**: Joanna, Matthew, Ruth, Stephen
- **Engine**: Neural (when available)
- **Language**: English (US)
- **Output Format**: MP3 for Manim integration

### 6. Service Architecture Updates

#### New AI Orchestrator Design
```python
class AIOrchestrator:
    async def generate_video_content(self, question: str, model: str) -> dict:
        # Stage 1: Initial explanation with user-selected model
        initial_explanation = await self.generate_initial_explanation(question, model)
        
        # Stage 2: GPT-5 refinement
        refined_explanation = await self.refine_explanation(initial_explanation)
        
        # Stage 3: Claude-4 script generation
        manim_script = await self.generate_manim_script(refined_explanation)
        
        # Stage 4: Claude-4 script validation
        validated_script = await self.validate_script(manim_script)
        
        return {
            "initial_explanation": initial_explanation,
            "refined_explanation": refined_explanation,
            "manim_script": validated_script
        }
```

#### S3 Upload Service
```python
class S3VideoService:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = "loli"
    
    async def upload_video(self, video_path: str, video_id: str, metadata: dict) -> str:
        # Upload video with metadata
        # Return public S3 URL
```

#### Enhanced Video Processor
```python
class VideoProcessor:
    async def process_video(self, script: str, video_id: str, voice: str, voiceover_text: str) -> str:
        # Generate video with Manim
        # Add voiceover using AWS Polly
        # Return local video path for S3 upload
```

### 7. Data Models Updates

#### Enhanced VideoRequest
```python
class VideoRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=10000)
    model: str = Field(..., description="AI model for initial explanation")
    voice: str = Field(default="Joanna", description="AWS Polly voice")
```

#### Enhanced VideoResponse  
```python
class VideoResponse(BaseModel):
    video_id: str
    status: VideoStatus
    message: str
    video_url: Optional[str] = None  # Legacy support
    s3_url: Optional[str] = None     # New S3 URL
    created_at: datetime
    progress: int = Field(ge=0, le=100)
    original_question: str
    initial_explanation: Optional[str] = None
    refined_explanation: Optional[str] = None
```

### 8. Configuration Updates

#### Environment Variables
```bash
# Existing AWS Configuration
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx  
AWS_REGION=eu-west-3

# New S3 Configuration
S3_BUCKET_NAME=loli

# Existing AI Model Configuration
OPENAI_API_KEY=xxx

# Processing Configuration (Keep Local)
MAX_CONCURRENT_VIDEOS=2
VIDEO_RETENTION_DAYS=7
TEMP_DIR=/tmp/manim_videos
```

#### Settings Class Updates
```python
class Settings(BaseSettings):
    # Existing settings...
    
    # S3 Configuration
    S3_BUCKET_NAME: str = "loli"
    
    # Force Claude-4 for script generation
    SCRIPT_GENERATION_MODEL: str = "claude-4-sonnet"
    SCRIPT_VALIDATION_MODEL: str = "claude-4-sonnet"
    REFINEMENT_MODEL: str = "gpt-5"
    
    # Available models for initial explanation
    EXPLANATION_MODELS: list = [
        "claude-3-5-sonnet",
        "claude-3-7-sonnet", 
        "claude-4-sonnet",
        "claude-3-sonnet",
        "claude-3-haiku"
    ]
```

## 🎯 Implementation Priority

### Phase 1: Core Pipeline Implementation
1. **Multi-stage AI processing pipeline**
2. **GPT-5 refinement integration**  
3. **Claude-4 script generation enforcement**
4. **Enhanced status tracking**

### Phase 2: S3 Integration
1. **S3 upload service creation**
2. **Public URL generation** 
3. **Metadata storage implementation**
4. **API response updates**

### Phase 3: Frontend Integration  
1. **New /api/v1/config endpoint**
2. **Enhanced status responses**
3. **S3 URL handling**
4. **React frontend updates**

### Phase 4: Testing and Polish
1. **End-to-end testing**
2. **Error handling refinement**
3. **Performance optimization**
4. **Documentation updates**

## 🚫 Removed Components

### Lambda Architecture (Completely Removed)
- ❌ AWS Lambda functions
- ❌ SQS job queues  
- ❌ DynamoDB job tracking
- ❌ CloudWatch integration
- ❌ Serverless processing

### Replaced Components
- ❌ Local video storage → ✅ S3 public URLs
- ❌ Single model processing → ✅ Multi-stage AI pipeline  
- ❌ Simple status tracking → ✅ Detailed progress tracking
- ❌ Basic API responses → ✅ Rich metadata responses

This architecture maintains the proven local processing approach while adding sophisticated AI processing and cloud storage capabilities for a superior educational video generation experience.
