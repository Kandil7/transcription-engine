// Mock API server for demonstration
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 8000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(multer().none());

// Mock data
let jobs = [
  {
    id: 'job_1',
    status: 'completed',
    progress: 100,
    message: 'Processing completed successfully',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    filename: 'sample_audio.mp3',
    duration: 120.5,
    language: 'ar',
    enable_translation: true,
    enable_summary: true,
    enable_voice_analytics: true,
    target_language: 'en',
    summary_length: 'medium'
  },
  {
    id: 'job_2',
    status: 'processing',
    progress: 45,
    message: 'Currently processing',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    filename: 'meeting_recording.wav',
    duration: 1800,
    language: 'en',
    enable_translation: false,
    enable_summary: true,
    enable_voice_analytics: false,
    target_language: null,
    summary_length: 'long'
  }
];

// API endpoints
app.get('/', (req, res) => {
  res.json({ message: 'Welcome to Transcription Engine API', version: '1.0.0' });
});

app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    version: '1.0.0',
    gpu_memory_gb: 24,
    cpu_cores: 8,
    environment: 'development'
  });
});

app.get('/api/v1/jobs/', (req, res) => {
  res.json(jobs);
});

app.get('/api/v1/jobs/:jobId', (req, res) => {
  const job = jobs.find(j => j.id === req.params.jobId);
  if (!job) {
    return res.status(404).json({ detail: 'Job not found' });
  }
  res.json(job);
});

app.get('/api/v1/jobs/:jobId/results', (req, res) => {
  const job = jobs.find(j => j.id === req.params.jobId);
  if (!job) {
    return res.status(404).json({ detail: 'Job not found' });
  }
  
  if (job.status !== 'completed') {
    return res.status(400).json({ detail: `Job is not completed. Current status: ${job.status}` });
  }
  
  res.json({
    id: job.id,
    transcript: `This is a mock transcript for ${job.filename}. The audio contains a conversation between multiple speakers discussing various topics. The content has been successfully transcribed with high accuracy.`,
    translation: job.enable_translation ? `This is a mock translation of the Arabic content to ${job.target_language}. The translation has been generated using advanced neural machine translation techniques.` : null,
    summary: job.enable_summary ? `This is a mock summary of the ${job.filename} content. The main points discussed include important topics and key decisions made during the meeting.` : null,
    hierarchical_summary: job.enable_summary ? {
      level_1_elevator_pitch: "Brief overview of the content in 30 seconds.",
      level_2_key_points: "Main points and decisions discussed.",
      level_3_comprehensive: "Detailed summary of all topics covered."
    } : null,
    voice_analytics: job.enable_voice_analytics ? {
      speaker_segments: [
        { speaker: 'Speaker 1', start: 0, end: 10, duration: 10, text: 'Hello everyone, welcome to the meeting.', emotion: 'neutral', confidence: 0.95 },
        { speaker: 'Speaker 2', start: 10, end: 25, duration: 15, text: 'Thanks for having me. Today we\'ll discuss the new project.', emotion: 'confident', confidence: 0.92 },
        { speaker: 'Speaker 1', start: 25, end: 40, duration: 15, text: 'Great, let\'s start with the objectives.', emotion: 'calm', confidence: 0.96 }
      ],
      meeting_analysis: {
        total_duration: job.duration,
        total_speakers: 2,
        dominant_speaker: 'Speaker 1',
        meeting_balance_score: 75,
        speaker_stats: {
          'Speaker 1': {
            total_speech_time: 25,
            speech_percentage: 62.5,
            segment_count: 2,
            avg_segment_length: 12.5,
            emotions: { calm: 1, neutral: 1 }
          },
          'Speaker 2': {
            total_speech_time: 15,
            speech_percentage: 37.5,
            segment_count: 1,
            avg_segment_length: 15,
            emotions: { confident: 1 }
          }
        }
      }
    } : null,
    subtitles_srt: job.enable_translation ? "1\n00:00:00,000 --> 00:00:10,000\nHello everyone, welcome to the meeting.\n\n2\n00:00:10,000 --> 00:00:25,000\nThanks for having me. Today we'll discuss the new project." : null,
    subtitles_vtt: job.enable_translation ? "WEBVTT FILE\n\n00:00:00.000 --> 00:00:10.000\nHello everyone, welcome to the meeting.\n\n00:00:10.000 --> 00:00:25.000\nThanks for having me. Today we'll discuss the new project." : null,
    audio_summary_url: null,
    processing_stats: {
      word_count: 120,
      language_confidence: 0.98,
      processing_time: 45
    }
  });
});

app.post('/api/v1/upload/file', (req, res) => {
  // Simulate file upload
  const jobId = `job_${Date.now()}`;
  const newJob = {
    id: jobId,
    status: 'processing',
    progress: 0,
    message: 'File uploaded successfully, processing started',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    filename: req.headers['x-filename'] || 'uploaded_file.mp3',
    duration: null,
    language: req.body.language || 'en',
    enable_translation: req.body.enable_translation === 'true',
    enable_summary: req.body.enable_summary === 'true',
    enable_voice_analytics: req.body.enable_voice_analytics === 'true',
    target_language: req.body.target_language || null,
    summary_length: req.body.summary_length || 'medium'
  };
  
  jobs.unshift(newJob);
  
  // Simulate processing
  setTimeout(() => {
    const jobIndex = jobs.findIndex(j => j.id === jobId);
    if (jobIndex !== -1) {
      jobs[jobIndex] = {
        ...jobs[jobIndex],
        status: 'completed',
        progress: 100,
        message: 'Processing completed successfully'
      };
    }
  }, 3000);
  
  // Simulate progress updates
  let progress = 0;
  const interval = setInterval(() => {
    progress += 10;
    const jobIndex = jobs.findIndex(j => j.id === jobId);
    if (jobIndex !== -1) {
      jobs[jobIndex] = {
        ...jobs[jobIndex],
        progress: progress,
        message: `Processing: ${progress}% complete`
      };
    }
    if (progress >= 100) {
      clearInterval(interval);
    }
  }, 500);
  
  res.json({ job_id: jobId });
});

app.post('/api/v1/qa/:jobId/ask', (req, res) => {
  const { question } = req.body || {};
  const jobId = req.params.jobId;
  
  res.json({
    answer: `This is a mock answer to your question: "${question}". Based on the transcript content, here are the relevant details.`,
    sources: [
      { text: 'Relevant text from the transcript that supports the answer.', chunk_id: 1 }
    ],
    confidence: 0.85,
    job_id: jobId
  });
});

app.listen(PORT, () => {
  console.log(`Mock API server running on http://localhost:${PORT}`);
});