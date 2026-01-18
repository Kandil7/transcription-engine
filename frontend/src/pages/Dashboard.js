import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  LinearProgress,
  Box
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import axios from 'axios';
import SkeletonLoader from '../components/SkeletonLoader';
import { getStatusColor } from '../utils/helpers';

function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await axios.get('/api/v1/jobs/');
      setJobs(response.data);
    } catch (error) {
      enqueueSnackbar('Failed to load jobs', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // The getStatusColor function is now available from the helpers utility

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <SkeletonLoader type="dashboard" />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1">
          Transcription Jobs
        </Typography>
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate('/upload')}
        >
          Upload New File
        </Button>
      </Box>

      <Grid container spacing={3}>
        {jobs.map((job) => (
          <Grid item xs={12} md={6} lg={4} key={job.id}>
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

                <Typography variant="body2" color="text.secondary" mb={1}>
                  Language: {job.language}
                </Typography>

                <Typography variant="body2" color="text.secondary" mb={2}>
                  Created: {new Date(job.created_at).toLocaleString()}
                </Typography>

                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => navigate(`/jobs/${job.id}`)}
                >
                  View Details
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {jobs.length === 0 && (
        <Box textAlign="center" mt={8}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No jobs yet
          </Typography>
          <Typography variant="body1" color="text.secondary" mb={3}>
            Upload your first audio or video file to get started
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/upload')}
          >
            Upload File
          </Button>
        </Box>
      )}
    </Container>
  );
}

export default Dashboard;