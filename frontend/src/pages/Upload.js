import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  LinearProgress,
  Alert
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import { useSnackbar } from 'notistack';
import axios from 'axios';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

function Upload() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [settings, setSettings] = useState({
    language: 'ar',
    enableTranslation: true,
    enableSummary: true,
    enableVoiceAnalytics: false,
    targetLanguage: 'en',
    summaryLength: 'medium'
  });

  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a'],
      'video/*': ['.mp4', '.avi', '.mov', '.mkv']
    },
    maxFiles: 1,
    maxSize: 500 * 1024 * 1024 // 500MB
  });

  const handleSettingChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleUpload = async () => {
    if (!file) {
      enqueueSnackbar('Please select a file first', { variant: 'warning' });
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', settings.language);
    formData.append('enable_translation', settings.enableTranslation.toString());
    formData.append('enable_summary', settings.enableSummary.toString());
    formData.append('enable_voice_analytics', settings.enableVoiceAnalytics.toString());
    formData.append('target_language', settings.targetLanguage);
    formData.append('summary_length', settings.summaryLength);

    setUploading(true);
    setProgress(0);

    try {
      const response = await axios.post('/api/v1/upload/file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percent);
        }
      });

      enqueueSnackbar('File uploaded successfully! Processing started.', { variant: 'success' });

      // Navigate to job details
      navigate(`/jobs/${response.data.job_id}`);

    } catch (error) {
      console.error('Upload error:', error);
      enqueueSnackbar(
        error.response?.data?.detail || 'Upload failed. Please try again.',
        { variant: 'error' }
      );
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Upload Audio/Video File
      </Typography>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed #ccc',
              borderRadius: 2,
              p: 6,
              textAlign: 'center',
              cursor: 'pointer',
              backgroundColor: isDragActive ? '#f5f5f5' : 'transparent',
              '&:hover': {
                backgroundColor: '#f5f5f5'
              }
            }}
          >
            <input {...getInputProps()} />
            <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop the file here' : 'Drag & drop a file here, or click to select'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Supported formats: MP3, WAV, MP4, AVI, MOV, MKV (max 500MB)
            </Typography>
          </Box>

          {file && (
            <Box mt={2}>
              <Typography variant="body1">
                Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(1)} MB)
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Processing Settings
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Source Language</InputLabel>
              <Select
                value={settings.language}
                label="Source Language"
                onChange={(e) => handleSettingChange('language', e.target.value)}
              >
                <MenuItem value="ar">Arabic</MenuItem>
                <MenuItem value="en">English</MenuItem>
                <MenuItem value="fr">French</MenuItem>
                <MenuItem value="de">German</MenuItem>
                <MenuItem value="es">Spanish</MenuItem>
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableTranslation}
                  onChange={(e) => handleSettingChange('enableTranslation', e.target.checked)}
                />
              }
              label="Enable Translation"
            />

            {settings.enableTranslation && (
              <FormControl fullWidth>
                <InputLabel>Target Language</InputLabel>
                <Select
                  value={settings.targetLanguage}
                  label="Target Language"
                  onChange={(e) => handleSettingChange('targetLanguage', e.target.value)}
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="ar">Arabic</MenuItem>
                  <MenuItem value="fr">French</MenuItem>
                  <MenuItem value="de">German</MenuItem>
                  <MenuItem value="es">Spanish</MenuItem>
                </Select>
              </FormControl>
            )}

            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableSummary}
                  onChange={(e) => handleSettingChange('enableSummary', e.target.checked)}
                />
              }
              label="Enable Summarization"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableVoiceAnalytics}
                  onChange={(e) => handleSettingChange('enableVoiceAnalytics', e.target.checked)}
                />
              }
              label="Enable Voice Analytics (Speaker Diarization & Emotion Detection)"
            />

            {settings.enableSummary && (
              <FormControl fullWidth>
                <InputLabel>Summary Length</InputLabel>
                <Select
                  value={settings.summaryLength}
                  label="Summary Length"
                  onChange={(e) => handleSettingChange('summaryLength', e.target.value)}
                >
                  <MenuItem value="short">Short</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="long">Long</MenuItem>
                </Select>
              </FormControl>
            )}
          </Box>
        </CardContent>
      </Card>

      {uploading && (
        <Box mb={4}>
          <Typography variant="body1" gutterBottom>
            Uploading... {progress}%
          </Typography>
          <LinearProgress variant="determinate" value={progress} />
        </Box>
      )}

      <Alert severity="info" sx={{ mb: 4 }}>
        <Typography variant="body2">
          Files are processed using AI models optimized for your hardware.
          Processing time depends on file length and available resources.
        </Typography>
      </Alert>

      <Box textAlign="center">
        <Button
          variant="contained"
          color="primary"
          size="large"
          onClick={handleUpload}
          disabled={!file || uploading}
        >
          {uploading ? 'Uploading...' : 'Start Processing'}
        </Button>
      </Box>
    </Container>
  );
}

export default Upload;