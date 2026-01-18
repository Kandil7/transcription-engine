import React from 'react';
import { Box, Container, Typography, Link, Grid } from '@mui/material';

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <Box
      component="footer"
      sx={{
        py: 4,
        px: 2,
        mt: 'auto',
        backgroundColor: 'background.paper',
        borderTop: (theme) => `1px solid ${theme.palette.divider}`,
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4} justifyContent="space-between">
          <Grid item xs={12} md={4}>
            <Typography variant="h6" gutterBottom>
              SoutiAI Transcription Engine
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Enterprise-grade AI transcription, translation, and analysis engine optimized for Arabic content.
            </Typography>
          </Grid>

          <Grid item xs={12} md={2}>
            <Typography variant="subtitle2" gutterBottom>
              Resources
            </Typography>
            <Box component="ul" sx={{ m: 0, p: 0, listStyle: 'none' }}>
              <li><Link href="/docs" target="_blank" underline="hover">API Docs</Link></li>
              <li><Link href="/help" underline="hover">Help Center</Link></li>
              <li><Link href="/settings" underline="hover">Settings</Link></li>
            </Box>
          </Grid>

          <Grid item xs={12} md={2}>
            <Typography variant="subtitle2" gutterBottom>
              Legal
            </Typography>
            <Box component="ul" sx={{ m: 0, p: 0, listStyle: 'none' }}>
              <li><Link href="#" underline="hover">Privacy Policy</Link></li>
              <li><Link href="#" underline="hover">Terms of Service</Link></li>
              <li><Link href="#" underline="hover">Licensing</Link></li>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Typography variant="subtitle2" gutterBottom>
              Contact Us
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Have questions? Reach out to our support team.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Email: <Link href="mailto:support@souti.ai">support@souti.ai</Link>
            </Typography>
          </Grid>
        </Grid>

        <Box
          sx={{
            pt: 3,
            mt: 3,
            borderTop: (theme) => `1px solid ${theme.palette.divider}`,
            textAlign: 'center',
          }}
        >
          <Typography variant="body2" color="text.secondary">
            © {currentYear} SoutiAI. All rights reserved. | Version 1.0.0
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default Footer;