import React from 'react';
import { Box, Typography, Button, Container } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import SentimentDissatisfiedIcon from '@mui/icons-material/SentimentDissatisfied';

function NotFound() {
    const navigate = useNavigate();

    return (
        <Container maxWidth="md" sx={{ mt: 8, textAlign: 'center' }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <SentimentDissatisfiedIcon sx={{ fontSize: 100, color: 'text.secondary', mb: 3 }} />
                <Typography variant="h2" gutterBottom color="primary">
                    404
                </Typography>
                <Typography variant="h4" gutterBottom>
                    Page Not Found
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                    The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
                </Typography>

                <Box sx={{ mt: 3 }}>
                    <Button
                        variant="contained"
                        color="primary"
                        size="large"
                        onClick={() => navigate('/')}
                        sx={{ mr: 2 }}
                    >
                        Go to Dashboard
                    </Button>
                    <Button
                        variant="outlined"
                        color="primary"
                        size="large"
                        onClick={() => navigate(-1)}
                    >
                        Go Back
                    </Button>
                </Box>
            </Box>
        </Container>
    );
}

export default NotFound;
