import React from 'react';
import { Card, CardContent, Box, Skeleton, Grid } from '@mui/material';

function SkeletonLoader({ type = 'job-card', count = 3 }) {
  const renderSkeleton = () => {
    switch (type) {
      case 'job-card':
        return Array.from({ length: count }).map((_, index) => (
          <Grid item xs={12} md={6} lg={4} key={index}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Skeleton variant="text" height={30} sx={{ mb: 2 }} />
                <Skeleton variant="rectangular" height={20} sx={{ mb: 1 }} />
                <Skeleton variant="rectangular" height={100} sx={{ mb: 2 }} />
                <Skeleton variant="rectangular" height={30} />
              </CardContent>
            </Card>
          </Grid>
        ));
      
      case 'transcript':
        return (
          <Card>
            <CardContent>
              <Skeleton variant="text" height={40} sx={{ mb: 2 }} />
              {Array.from({ length: 5 }).map((_, index) => (
                <Skeleton key={index} variant="text" height={20} sx={{ mb: 1 }} />
              ))}
            </CardContent>
          </Card>
        );
      
      case 'dashboard':
        return (
          <Grid container spacing={3}>
            {Array.from({ length: 3 }).map((_, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Card>
                  <CardContent>
                    <Skeleton variant="text" height={30} sx={{ mb: 1 }} />
                    <Skeleton variant="text" height={50} />
                  </CardContent>
                </Card>
              </Grid>
            ))}
            
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Skeleton variant="text" height={40} sx={{ mb: 2 }} />
                  <Grid container spacing={2}>
                    {Array.from({ length: 6 }).map((_, index) => (
                      <Grid item xs={12} sm={6} md={4} key={index}>
                        <Skeleton variant="rectangular" height={100} />
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        );
      
      default:
        return <Skeleton variant="rectangular" height={100} />;
    }
  };

  return <>{renderSkeleton()}</>;
}

export default SkeletonLoader;