# 🔧 Technical Specifications & Implementation Guide

## 🏗️ Architecture Overview

### Current vs. Target Architecture

#### **🚀 UPDATED: Lambda-First Architecture**

#### Current Architecture
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

#### Corrected Lambda-First Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Lovable       │    │   FastAPI        │    │ AWS Bedrock +   │
│   React App     │────│   Orchestrator   │────│ OpenAI ChatGPT-5│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        ▼
                                │               ┌─────────────────┐
                                │               │  Generated      │
                                │               │  Manim Script   │
                                │               └─────────────────┘
                                ▼                        │
                    ┌─────────────────┐                 │
                    │   SQS Queue     │◄────────────────┘
                    │   Video Jobs    │
                    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   AWS Lambda    │────│   DynamoDB      │
                    │   Video Gen     │    │   Job Status    │
                    └─────────────────┘    └─────────────────┘
                                │                     ▲
                                ▼                     │
                    ┌─────────────────┐               │
                    │  AWS Polly +    │               │
                    │  Manim Engine   │               │
                    └─────────────────┘               │
                                │                     │
                                ▼                     │
                    ┌─────────────────┐               │
                    │  S3 Storage +   │───────────────┘
                    │  CloudWatch     │
                    └─────────────────┘
```

**Flow Explanation:**
1. React Frontend sends video request to FastAPI
2. FastAPI calls AI models (Bedrock/ChatGPT-5) to generate Manim script
3. FastAPI submits job with script to SQS queue
4. Lambda picks up job, processes video with Manim + Polly
5. Lambda updates DynamoDB with progress and stores video in S3
6. Frontend polls FastAPI which checks DynamoDB for status updates
```

## 📦 Technical Specifications

### 1. AWS Bedrock Integration

#### Purpose and Goals
Replace the current Google Gemini integration with AWS Bedrock to access multiple large language models through a single API. This gives us access to Claude, Llama, Titan, and other models while staying within the AWS ecosystem.

#### Key Requirements
- Support for multiple model providers (Anthropic Claude, Meta Llama, Amazon Titan)
- Model-specific request formatting since each model has different API requirements
- Intelligent model selection based on prompt complexity and cost considerations
- Cost tracking and optimization to stay within budget limits
- Fallback mechanisms if preferred models are unavailable or over budget

#### Integration Approach
Create a unified Bedrock service that handles all the different model formats internally, so the rest of the application just asks for a script and gets one back. The service should automatically choose the best model based on the complexity of the educational content requested.

### 2. Multi-Model AI Orchestrator

#### Purpose and Goals
Create a smart layer that can call both AWS Bedrock models and OpenAI ChatGPT-5, then intelligently route requests based on content complexity, cost, and model availability. This gives users the best of both worlds.

#### Key Requirements
- Support for both AWS Bedrock and OpenAI API calls
- Smart model selection algorithm that analyzes prompt complexity
- Cost tracking across all models to prevent budget overruns
- Model performance comparison and quality scoring
- Real-time model availability checking

#### Decision Logic
Simple prompts go to cost-effective models like Llama, complex educational content goes to Claude or ChatGPT-5, and mathematical proofs or advanced topics get routed to the highest quality models regardless of cost.

### 3. AWS Polly Integration

#### Purpose and Goals
Replace Azure Text-to-Speech with AWS Polly to generate high-quality neural voices for video narration. This keeps everything in the AWS ecosystem and gives us access to better voice options and SSML markup for natural-sounding speech.

#### Key Requirements
- Support for multiple neural voices with different styles (friendly, professional, educational)
- SSML markup support for better pronunciation and pacing
- Multiple language support for international content
- Integration with the Lambda video processing pipeline
- Voice selection interface for users to choose their preferred narrator

#### Voice Strategy
Provide a curated selection of high-quality neural voices that work well for educational content. Include both male and female options with different regional accents. Use SSML to add natural pauses and emphasis for better listening experience.

### 4. OpenAI ChatGPT-5 Integration

#### Purpose and Goals
Integrate OpenAI's latest ChatGPT-5 model as a premium option for generating high-quality educational content. This gives users access to the most advanced AI model available while maintaining the option to use more cost-effective AWS Bedrock models.

#### Key Requirements
- Direct integration with OpenAI API for ChatGPT-5 access
- Specialized system prompts optimized for Manim script generation
- Cost tracking and usage monitoring since this is the most expensive option
- Quality comparison metrics against Bedrock models
- Fallback to Bedrock models if OpenAI API is unavailable

#### Integration Strategy
Position ChatGPT-5 as the premium option for complex educational content, advanced mathematical concepts, and when users specifically want the highest quality output regardless of cost. Use it for comparison demonstrations in the hackathon demo.

### 5. AWS Lambda Video Processing

#### Purpose and Goals
Replace the current local subprocess-based video processing with pure AWS Lambda functions. This eliminates the need for always-running servers, provides infinite scalability, and creates a true pay-per-use cost model.

#### Key Requirements
- Complete Manim environment in Lambda with all required dependencies
- Integration with AWS Polly for voiceover generation within Lambda
- Automatic scaling to handle multiple video requests simultaneously
- Progress tracking and status updates via DynamoDB
- Video storage and delivery through S3 with presigned URLs
- Error handling and retry mechanisms for failed video generations

#### Processing Flow
Lambda receives a job from SQS containing the generated Manim script and voice configuration. It sets up a temporary environment, runs Manim to generate the video, adds voiceover using Polly, uploads the final video to S3, and updates DynamoDB with completion status and download URLs.

### 6. SQS Job Queue System

#### Purpose and Goals
Implement a reliable job queue system that can handle multiple video processing requests without overwhelming the Lambda functions or losing jobs during high traffic periods.

#### Key Requirements
- Message persistence to prevent job loss during system failures
- Dead letter queue for failed jobs that can be investigated and retried
- Batch processing capabilities for efficiency
- Message visibility timeout management to prevent duplicate processing
- Integration with CloudWatch for monitoring queue depth and processing times

#### Queue Strategy
Use standard SQS queues with appropriate visibility timeouts that match Lambda processing times. Implement dead letter queues for jobs that fail multiple times, allowing for manual investigation and reprocessing.

### 7. DynamoDB Job Tracking

#### Purpose and Goals
Provide real-time job status tracking that allows users to check on their video generation progress without directly polling Lambda functions or overwhelming the system.

#### Key Requirements
- Real-time status updates (queued, processing, completed, failed)
- Progress tracking with percentage completion
- Error message storage for debugging failed jobs
- Job metadata including creation time, completion time, and processing duration
- Cost tracking per job for analytics and billing
- TTL (Time To Live) for automatic cleanup of old job records

#### Data Strategy
Store job records with video_id as the primary key, include all relevant metadata, and use DynamoDB streams to trigger notifications or analytics updates when job status changes.

### 8. Lovable React Frontend

#### Purpose and Goals
Create a modern, beautiful, and responsive React application that showcases the platform's capabilities and provides an excellent user experience for creating and managing educational videos.

#### Key Features Required
- Video creation form with AI model selection (Bedrock vs ChatGPT-5)
- Voice selection interface with preview capabilities
- Real-time progress tracking with live status updates
- Video gallery with thumbnail previews and download options
- Cost calculator showing estimated costs vs traditional solutions
- Processing analytics dashboard showing system performance
- Model comparison interface for hackathon demonstrations

#### Technical Requirements
- Responsive design that works on desktop, tablet, and mobile
- Real-time updates using polling or WebSocket connections
- Modern UI components with smooth animations and transitions
- Accessibility compliance for educational use
- Fast loading times with optimized assets
- Integration with the FastAPI backend through clean API calls

#### User Experience Goals
Make video creation feel magical and effortless while providing transparency into the AI model selection and processing pipeline. Users should understand the value of the serverless architecture through clear cost comparisons and performance metrics.

### 9. Configuration Management

#### Purpose and Goals
Centralize all configuration settings for AWS services, AI models, and application behavior in a clean, environment-variable-driven system that works for both development and production.

#### Key Configuration Areas
- AWS service credentials and region settings
- AI model selection and API keys for both Bedrock and OpenAI
- Cost management thresholds and budget controls
- Voice and language preferences for Polly
- Lambda function settings and timeouts
- Database and storage configuration

#### Environment Strategy
Use environment variables for all sensitive data like API keys, with sensible defaults for non-sensitive settings. Support both development (.env file) and production (environment variables) deployment patterns.

## 🎯 Implementation Priorities

### Phase 1: Foundation 
**Goal: Get the core AWS integrations working while keeping the current system operational**

1. **AWS Bedrock Integration** - Add multi-model AI capability alongside existing Gemini
2. **AWS Polly Integration** - Replace Azure TTS with AWS Polly
3. **Basic Model Selection** - Allow users to choose between AI models
4. **Configuration Setup** - Environment variables and AWS credentials

### Phase 2: Lambda Transition
**Goal: Build and test the Lambda video processing pipeline**

1. **Lambda Function Development** - Create the serverless video processing function
2. **SQS Queue Setup** - Implement job queue system
3. **DynamoDB Integration** - Add job status tracking
4. **S3 Storage** - Video storage and delivery system

### Phase 3: Frontend and Polish 
**Goal: Create beautiful user interface and prepare for demo**

1. **Lovable React Frontend** - Modern, responsive user interface
2. **Real-time Status Updates** - Live progress tracking
3. **Cost Analytics** - Usage dashboards and comparisons
4. **Demo Preparation** - Impressive showcase content

### Phase 4: Final Integration 
**Goal: Replace local processing with Lambda and prepare winning demo**

1. **Remove Local Processing** - Complete transition to pure Lambda
2. **Performance Testing** - Ensure system handles multiple concurrent requests
3. **Demo Content Creation** - Prepare impressive demonstration videos
4. **Presentation Materials** - Architecture diagrams and talking points

This specification provides clear goals and requirements for each component without getting bogged down in implementation details. The focus is on understanding what needs to be built and why, leaving the how for the actual implementation phase.
