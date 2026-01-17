import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Box,
  Button,
  Chip,
  LinearProgress,
  Alert,
  Paper,
  Divider,
  IconButton,
  Grid
} from '@mui/material';
import { useSnackbar } from 'notistack';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import StopIcon from '@mui/icons-material/Stop';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

function Streaming() {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId] = useState(() => `stream_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [transcription, setTranscription] = useState('');
  const [segments, setSegments] = useState([]);
  const [language, setLanguage] = useState('ar');
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [finalResults, setFinalResults] = useState(null);

  const websocketRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      stopRecording();
      disconnectWebSocket();
    };
  }, []);

  const connectWebSocket = () => {
    if (websocketRef.current) {
      return; // Already connected
    }

    try {
      const wsUrl = `ws://localhost:8000/api/v1/ws/stream/${sessionId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        setConnectionStatus('connected');
        enqueueSnackbar('Connected to streaming service', { variant: 'success' });
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'session_started':
            setConnectionStatus('ready');
            enqueueSnackbar('Streaming session started', { variant: 'info' });
            break;

          case 'transcription_chunk':
            handleTranscriptionChunk(data);
            break;

          case 'session_ended':
            handleSessionEnded(data);
            break;

          case 'error':
            enqueueSnackbar(`Streaming error: ${data.message}`, { variant: 'error' });
            break;

          default:
            console.log('Unknown message type:', data.type);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        setConnectionStatus('disconnected');
        setIsRecording(false);
        enqueueSnackbar('Disconnected from streaming service', { variant: 'warning' });
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
        enqueueSnackbar('WebSocket connection error', { variant: 'error' });
      };

      websocketRef.current = ws;

    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      enqueueSnackbar('Failed to connect to streaming service', { variant: 'error' });
    }
  };

  const disconnectWebSocket = () => {
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    setIsConnected(false);
    setConnectionStatus('disconnected');
  };

  const startRecording = async () => {
    try {
      // First ensure WebSocket is connected
      if (!isConnected) {
        await connectWebSocket();
        // Wait a bit for connection
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        }
      });

      streamRef.current = stream;

      // Create MediaRecorder for WAV format
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      mediaRecorderRef.current = mediaRecorder;

      // Collect audio data
      const audioChunks = [];
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        if (audioChunks.length > 0) {
          // Convert to WAV and send final chunk
          convertToWav(audioChunks).then(wavBlob => {
            if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
              wavBlob.arrayBuffer().then(buffer => {
                websocketRef.current.send(buffer);
              });
            }
          });
        }
      };

      // Start recording and sending chunks
      mediaRecorder.start(1000); // Collect data every second
      setIsRecording(true);
      enqueueSnackbar('Recording started', { variant: 'success' });

      // Send chunks periodically
      const sendInterval = setInterval(() => {
        if (mediaRecorder.state === 'recording' && websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
          mediaRecorder.requestData();
        }
      }, 2000); // Send every 2 seconds

      // Store interval for cleanup
      mediaRecorder.sendInterval = sendInterval;

    } catch (error) {
      console.error('Failed to start recording:', error);
      enqueueSnackbar('Failed to access microphone', { variant: 'error' });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      clearInterval(mediaRecorderRef.current.sendInterval);
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    setIsRecording(false);
    enqueueSnackbar('Recording stopped', { variant: 'info' });
  };

  const convertToWav = async (chunks) => {
    // Convert WebM chunks to WAV (simplified - in production use a proper library)
    const audioBlob = new Blob(chunks, { type: 'audio/webm' });
    return audioBlob; // Placeholder - real conversion needed
  };

  const handleTranscriptionChunk = (data) => {
    const segment = data.segment;

    setSegments(prev => [...prev, segment]);
    setTranscription(prev => prev + ' ' + segment.text);
  };

  const handleSessionEnded = (data) => {
    setFinalResults(data.final_results);
    setConnectionStatus('completed');
    enqueueSnackbar('Streaming session completed', { variant: 'success' });
  };

  const saveAsJob = () => {
    if (!finalResults) return;

    // Navigate to upload page with streaming results
    navigate('/upload', {
      state: {
        streamingResults: finalResults,
        language: language
      }
    });
  };

  const getStatusColor = (status) => {
    const colors = {
      disconnected: 'error',
      connecting: 'warning',
      connected: 'info',
      ready: 'success',
      error: 'error',
      completed: 'success'
    };
    return colors[status] || 'default';
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Real-time Streaming Transcription
      </Typography>

      <Alert severity="info" sx={{ mb: 4 }}>
        <Typography variant="body2">
          Start recording to get live transcription as you speak. Perfect for meetings, lectures, or real-time captioning.
        </Typography>
      </Alert>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Connection Status
              </Typography>

              <Box sx={{ mb: 2 }}>
                <Chip
                  label={connectionStatus}
                  color={getStatusColor(connectionStatus)}
                  size="small"
                />
              </Box>

              <Typography variant="body2" color="text.secondary" gutterBottom>
                Session ID: {sessionId}
              </Typography>

              <Typography variant="body2" color="text.secondary" gutterBottom>
                Language: {language}
              </Typography>

              <Typography variant="body2" color="text.secondary" gutterBottom>
                Segments: {segments.length}
              </Typography>

              <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 1 }}>
                {!isConnected && (
                  <Button
                    variant="outlined"
                    onClick={connectWebSocket}
                    fullWidth
                  >
                    Connect
                  </Button>
                )}

                {isConnected && !isRecording && connectionStatus === 'ready' && (
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<MicIcon />}
                    onClick={startRecording}
                    fullWidth
                  >
                    Start Recording
                  </Button>
                )}

                {isRecording && (
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<MicOffIcon />}
                    onClick={stopRecording}
                    fullWidth
                  >
                    Stop Recording
                  </Button>
                )}

                {isConnected && (
                  <Button
                    variant="outlined"
                    color="secondary"
                    onClick={disconnectWebSocket}
                    fullWidth
                  >
                    Disconnect
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Live Transcription
              </Typography>

              {isRecording && (
                <Box sx={{ mb: 2 }}>
                  <LinearProgress />
                  <Typography variant="caption" color="text.secondary">
                    Recording and transcribing in real-time...
                  </Typography>
                </Box>
              )}

              <Paper
                sx={{
                  p: 2,
                  minHeight: 200,
                  maxHeight: 400,
                  overflow: 'auto',
                  backgroundColor: '#f5f5f5',
                  fontFamily: 'monospace'
                }}
              >
                {transcription || 'Transcription will appear here as you speak...'}
              </Paper>

              {segments.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Segments ({segments.length})
                  </Typography>
                  <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                    {segments.map((segment, index) => (
                      <Box key={segment.key || index} sx={{ mb: 1, p: 1, backgroundColor: '#fafafa', borderRadius: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          {segment.start?.toFixed(1)}s - {segment.end?.toFixed(1)}s
                        </Typography>
                        <Typography variant="body2">
                          {segment.text}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>

          {finalResults && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Session Complete
                </Typography>

                <Typography variant="body2" gutterBottom>
                  Total segments: {finalResults.total_segments}
                </Typography>

                <Typography variant="body2" gutterBottom>
                  Duration: {finalResults.total_duration_seconds?.toFixed(1)} seconds
                </Typography>

                <Box sx={{ mt: 2 }}>
                  <Button
                    variant="contained"
                    startIcon={<PlayArrowIcon />}
                    onClick={saveAsJob}
                  >
                    Save as Job
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Container>
  );
}

export default Streaming;