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
  Alert
} from '@mui/material';
import { useSnackbar } from 'notistack';
import axios from 'axios';
import DownloadIcon from '@mui/icons-material/Download';

function JobDetails() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
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