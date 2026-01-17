import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Box,
  Button,
  Grid,
  Divider,
  Alert,
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress
} from '@mui/material';
import { useSnackbar } from 'notistack';
import axios from 'axios';
import DownloadIcon from '@mui/icons-material/Download';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';

function JobDetails() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [answers, setAnswers] = useState([]);
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    fetchJobDetails();
    // Set up polling for job status updates
    const interval = setInterval(fetchJobDetails, 5000);
    return () => clearInterval(interval);
  }, [jobId]);

  const fetchJobDetails = async () => {
    try {
      const response = await axios.get(`/api/v1/jobs/${jobId}`);
      setJob(response.data);

      // If job is completed, fetch results
      if (response.data.status === 'completed') {
        const resultsResponse = await axios.get(`/api/v1/jobs/${jobId}/results`);
        setResults(resultsResponse.data);
      }
    } catch (error) {
      enqueueSnackbar('Failed to load job details', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const askQuestion = async () => {
    if (!question.trim()) {
      enqueueSnackbar('Please enter a question', { variant: 'warning' });
      return;
    }

    setAsking(true);
    try {
      const response = await axios.post(`/api/v1/qa/${jobId}/ask`, {
        question: question.trim()
      });

      const newAnswer = {
        id: Date.now(),
        question: question.trim(),
        ...response.data,
        timestamp: new Date().toLocaleString()
      };

      setAnswers(prev => [newAnswer, ...prev]);
      setQuestion('');

    } catch (error) {
      enqueueSnackbar('Failed to get answer', { variant: 'error' });
    } finally {
      setAsking(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'warning',
      processing: 'info',
      completed: 'success',
      failed: 'error',
      cancelled: 'default'
    };
    return colors[status] || 'default';
  };

  const handleDownload = (content, filename, mimeType = 'text/plain') => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography>Loading job details...</Typography>
      </Container>
    );
  }

  if (!job) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">Job not found</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Job Details
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {job.filename}
              </Typography>

              <Box mb={2}>
                <Chip
                  label={job.status}
                  color={getStatusColor(job.status)}
                  size="small"
                />
              </Box>

              {job.progress !== null && job.progress !== undefined && (
                <Box mb={2}>
                  <LinearProgress
                    variant="determinate"
                    value={job.progress}
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {job.progress}% complete
                  </Typography>
                </Box>
              )}

              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Language
                  </Typography>
                  <Typography variant="body1">{job.language}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Created
                  </Typography>
                  <Typography variant="body1">
                    {new Date(job.created_at).toLocaleString()}
                  </Typography>
                </Grid>
                {job.duration && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Duration
                    </Typography>
                    <Typography variant="body1">
                      {Math.round(job.duration)}s
                    </Typography>
                  </Grid>
                )}
              </Grid>

              {job.message && (
                <Alert severity={job.status === 'failed' ? 'error' : 'info'} sx={{ mb: 2 }}>
                  {job.message}
                </Alert>
              )}
            </CardContent>
          </Card>

          {results && (
            <>
              <Card sx={{ mt: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Transcript
                  </Typography>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {results.transcript}
                  </Typography>
                </CardContent>
              </Card>

              {results.translation && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Translation ({job.target_language})
                    </Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {results.translation}
                    </Typography>
                  </CardContent>
                </Card>
              )}

              {results.summary && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Summary
                    </Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {results.summary}
                    </Typography>
                  </CardContent>
                </Card>
              )}

              {results.hierarchical_summary && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Hierarchical Summary
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Multiple levels of summarization for different needs
                    </Typography>

                    <Box sx={{ mt: 2 }}>
                      {results.hierarchical_summary.level_1_elevator_pitch && (
                        <Box sx={{ mb: 3 }}>
                          <Typography variant="subtitle1" color="primary" gutterBottom>
                            📄 Elevator Pitch (30 seconds read)
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', pl: 2 }}>
                            {results.hierarchical_summary.level_1_elevator_pitch}
                          </Typography>
                        </Box>
                      )}

                      {results.hierarchical_summary.level_2_key_points && (
                        <Box sx={{ mb: 3 }}>
                          <Typography variant="subtitle1" color="primary" gutterBottom>
                            🎯 Key Points (2 minutes read)
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', pl: 2 }}>
                            {results.hierarchical_summary.level_2_key_points}
                          </Typography>
                        </Box>
                      )}

                      {results.hierarchical_summary.level_3_comprehensive && (
                        <Box sx={{ mb: 3 }}>
                          <Typography variant="subtitle1" color="primary" gutterBottom>
                            📚 Comprehensive Summary (5+ minutes read)
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', pl: 2 }}>
                            {results.hierarchical_summary.level_3_comprehensive}
                          </Typography>
                        </Box>
                      )}
                    </Box>

                    {results.hierarchical_summary.metadata && (
                      <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          Generated using {results.hierarchical_summary.metadata.method} •
                          Original text: {results.hierarchical_summary.metadata.original_length} characters •
                          {results.hierarchical_summary.metadata.levels_generated} summary levels
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              )}

              {results && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <QuestionAnswerIcon sx={{ mr: 1 }} />
                      Ask Questions About Your Content
                    </Typography>

                    <Box sx={{ mb: 3 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={9}>
                          <TextField
                            fullWidth
                            label="Ask a question about this transcript"
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && askQuestion()}
                            placeholder="e.g., What are the main points discussed?"
                          />
                        </Grid>
                        <Grid item xs={3}>
                          <Button
                            fullWidth
                            variant="contained"
                            onClick={askQuestion}
                            disabled={asking || !question.trim()}
                            sx={{ height: 56 }}
                          >
                            {asking ? <CircularProgress size={24} /> : 'Ask'}
                          </Button>
                        </Grid>
                      </Grid>
                    </Box>

                    {answers.length > 0 && (
                      <Box>
                        <Typography variant="subtitle1" gutterBottom>
                          Previous Questions & Answers
                        </Typography>
                        {answers.map((answer) => (
                          <Accordion key={answer.id} sx={{ mb: 1 }}>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                              <Box sx={{ width: '100%' }}>
                                <Typography variant="subtitle2">
                                  Q: {answer.question}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {answer.timestamp} • Confidence: {(answer.confidence * 100).toFixed(0)}%
                                </Typography>
                              </Box>
                            </AccordionSummary>
                            <AccordionDetails>
                              <Typography variant="body1" paragraph>
                                <strong>Answer:</strong> {answer.answer}
                              </Typography>

                              {answer.sources && answer.sources.length > 0 && (
                                <Box>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Sources:
                                  </Typography>
                                  {answer.sources.map((source, index) => (
                                    <Box key={index} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                                      <Typography variant="body2">
                                        {source.text}
                                      </Typography>
                                      {source.chunk_id !== undefined && (
                                        <Typography variant="caption" color="text.secondary">
                                          Chunk {source.chunk_id}
                                        </Typography>
                                      )}
                                    </Box>
                                  ))}
                                </Box>
                              )}
                            </AccordionDetails>
                          </Accordion>
                        ))}
                      </Box>
                    )}

                    <Alert severity="info" sx={{ mt: 2 }}>
                      <Typography variant="body2">
                        Ask questions in Arabic or English about the content of your transcript.
                        The AI will search through the entire transcript to provide accurate answers with source references.
                      </Typography>
                    </Alert>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Downloads
              </Typography>

              {results && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {results.transcript && (
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(results.transcript, 'transcript.txt')}
                      fullWidth
                    >
                      Transcript
                    </Button>
                  )}

                  {results.translation && (
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(results.translation, 'translation.txt')}
                      fullWidth
                    >
                      Translation
                    </Button>
                  )}

                  {results.summary && (
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(results.summary, 'summary.txt')}
                      fullWidth
                    >
                      Summary
                    </Button>
                  )}

                  {results.subtitles_srt && (
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(results.subtitles_srt, 'subtitles.srt')}
                      fullWidth
                    >
                      SRT Subtitles
                    </Button>
                  )}

                  {results.subtitles_vtt && (
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(results.subtitles_vtt, 'subtitles.vtt')}
                      fullWidth
                    >
                      VTT Subtitles
                    </Button>
                  )}
                </Box>
              )}

              {!results && job.status !== 'completed' && (
                <Typography variant="body2" color="text.secondary">
                  Downloads will be available once processing is complete.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

export default JobDetails;