# React Search Implementation Guide

## Overview
This guide shows how to implement the unified search functionality for the talent platform dashboard using React. The search system supports multiple profile types with advanced filtering and pagination.

## API Endpoints
```
Base URL: /api/dashboard/
- Search: GET /search/
- Profile Details:
  - Talent: GET /profiles/talent/{id}/
  - Visual: GET /profiles/visual/{id}/
  - Expressive: GET /profiles/expressive/{id}/
  - Hybrid: GET /profiles/hybrid/{id}/
  - Band: GET /profiles/band/{id}/
```

## 1. Project Structure
```
src/
  components/
    search/
      SearchContainer.tsx
      SearchBar.tsx
      FilterPanel.tsx
      SearchResults.tsx
      ProfileCard.tsx
      PaginationControls.tsx
  hooks/
    useSearch.ts
    useDebounce.ts
  services/
    searchApi.ts
  types/
    search.types.ts
  utils/
    searchHelpers.ts
```

## 2. TypeScript Types

```typescript
// src/types/search.types.ts
export interface SearchParams {
  profile_type: ProfileType;
  page?: number;
  page_size?: number;
  [key: string]: any;
}

export type ProfileType = 
  | 'talent' 
  | 'visual' 
  | 'expressive' 
  | 'hybrid' 
  | 'bands' 
  | 'background' 
  | 'props' 
  | 'costumes' 
  | 'memorabilia' 
  | 'vehicles' 
  | 'artistic_materials' 
  | 'music_items' 
  | 'rare_items';

export interface SearchResult {
  id: number;
  relevance_score: number;
  profile_score: number;
  profile_url: string;
  [key: string]: any;
}

export interface SearchResponse {
  success: boolean;
  profile_type: string;
  count: number;
  search_criteria: Record<string, any>;
  results: SearchResult[];
  next?: string;
  previous?: string;
}

export interface TalentSearchParams extends SearchParams {
  gender?: 'Male' | 'Female' | 'Other';
  city?: string;
  country?: string;
  account_type?: 'free' | 'silver' | 'gold' | 'platinum';
  is_verified?: boolean;
  age?: number;
  specialization?: 'visual' | 'expressive' | 'hybrid';
}

export interface VisualWorkerSearchParams extends SearchParams {
  primary_category?: string;
  experience_level?: string;
  min_years_experience?: number;
  max_years_experience?: number;
  city?: string;
  country?: string;
  availability?: string;
  rate_range?: string;
  willing_to_relocate?: boolean;
}

export interface ExpressiveWorkerSearchParams extends SearchParams {
  performer_type?: string;
  min_years_experience?: number;
  max_years_experience?: number;
  hair_color?: string;
  eye_color?: string;
  body_type?: string;
  height?: number;
  weight?: number;
  city?: string;
  country?: string;
  availability?: string;
  height_tolerance?: number;
  weight_tolerance?: number;
}
```

## 3. API Service

```typescript
// src/services/searchApi.ts
import axios from 'axios';
import { SearchParams, SearchResponse } from '../types/search.types';

const API_BASE_URL = '/api/dashboard';

// Create axios instance with auth
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const searchApi = {
  // Main search function
  search: async (params: SearchParams): Promise<SearchResponse> => {
    try {
      const response = await apiClient.get('/search/', { params });
      return response.data;
    } catch (error) {
      console.error('Search API error:', error);
      throw error;
    }
  },

  // Get profile details
  getProfileDetails: async (profileType: string, id: number) => {
    try {
      const response = await apiClient.get(`/profiles/${profileType}/${id}/`);
      return response.data;
    } catch (error) {
      console.error('Profile details API error:', error);
      throw error;
    }
  },
};
```

## 4. Custom Hooks

```typescript
// src/hooks/useDebounce.ts
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

```typescript
// src/hooks/useSearch.ts
import { useState, useEffect, useCallback } from 'react';
import { searchApi } from '../services/searchApi';
import { SearchParams, SearchResponse, ProfileType } from '../types/search.types';
import { useDebounce } from './useDebounce';

export const useSearch = (initialProfileType: ProfileType = 'talent') => {
  const [searchParams, setSearchParams] = useState<SearchParams>({
    profile_type: initialProfileType,
    page: 1,
    page_size: 20,
  });
  
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Debounce search params to avoid too many API calls
  const debouncedParams = useDebounce(searchParams, 300);

  const performSearch = useCallback(async (params: SearchParams) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await searchApi.search(params);
      setResults(response);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Search failed');
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Trigger search when debounced params change
  useEffect(() => {
    performSearch(debouncedParams);
  }, [debouncedParams, performSearch]);

  const updateSearchParams = useCallback((newParams: Partial<SearchParams>) => {
    setSearchParams(prev => ({
      ...prev,
      ...newParams,
      page: newParams.page || 1, // Reset to page 1 unless explicitly setting page
    }));
  }, []);

  const resetSearch = useCallback(() => {
    setSearchParams({
      profile_type: initialProfileType,
      page: 1,
      page_size: 20,
    });
  }, [initialProfileType]);

  const loadNextPage = useCallback(() => {
    if (results?.next) {
      updateSearchParams({ page: (searchParams.page || 1) + 1 });
    }
  }, [results?.next, searchParams.page, updateSearchParams]);

  const loadPreviousPage = useCallback(() => {
    if (results?.previous && (searchParams.page || 1) > 1) {
      updateSearchParams({ page: (searchParams.page || 1) - 1 });
    }
  }, [results?.previous, searchParams.page, updateSearchParams]);

  return {
    searchParams,
    results,
    loading,
    error,
    updateSearchParams,
    resetSearch,
    loadNextPage,
    loadPreviousPage,
    performSearch: () => performSearch(searchParams),
  };
};
```

## 5. Components

```tsx
// src/components/search/SearchContainer.tsx
import React, { useState } from 'react';
import { Box, Container, Typography, Alert } from '@mui/material';
import { ProfileType } from '../../types/search.types';
import { useSearch } from '../../hooks/useSearch';
import SearchBar from './SearchBar';
import FilterPanel from './FilterPanel';
import SearchResults from './SearchResults';
import PaginationControls from './PaginationControls';

const SearchContainer: React.FC = () => {
  const [selectedProfileType, setSelectedProfileType] = useState<ProfileType>('talent');
  const {
    searchParams,
    results,
    loading,
    error,
    updateSearchParams,
    resetSearch,
    loadNextPage,
    loadPreviousPage,
  } = useSearch(selectedProfileType);

  const handleProfileTypeChange = (profileType: ProfileType) => {
    setSelectedProfileType(profileType);
    updateSearchParams({ profile_type: profileType });
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Talent Search
        </Typography>

        <SearchBar
          profileType={selectedProfileType}
          onProfileTypeChange={handleProfileTypeChange}
          onSearch={updateSearchParams}
          onReset={resetSearch}
        />

        <Box sx={{ display: 'flex', gap: 3, mt: 3 }}>
          <Box sx={{ width: 300, flexShrink: 0 }}>
            <FilterPanel
              profileType={selectedProfileType}
              currentFilters={searchParams}
              onFiltersChange={updateSearchParams}
            />
          </Box>

          <Box sx={{ flex: 1 }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <SearchResults
              results={results}
              loading={loading}
              profileType={selectedProfileType}
            />

            {results && (
              <PaginationControls
                currentPage={searchParams.page || 1}
                totalCount={results.count}
                pageSize={searchParams.page_size || 20}
                hasNext={!!results.next}
                hasPrevious={!!results.previous}
                onNextPage={loadNextPage}
                onPreviousPage={loadPreviousPage}
              />
            )}
          </Box>
        </Box>
      </Box>
    </Container>
  );
};

export default SearchContainer;
```

```tsx
// src/components/search/SearchBar.tsx
import React, { useState } from 'react';
import {
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Paper,
} from '@mui/material';
import { Search, Clear } from '@mui/icons-material';
import { ProfileType, SearchParams } from '../../types/search.types';

interface SearchBarProps {
  profileType: ProfileType;
  onProfileTypeChange: (profileType: ProfileType) => void;
  onSearch: (params: Partial<SearchParams>) => void;
  onReset: () => void;
}

const profileTypes: { value: ProfileType; label: string }[] = [
  { value: 'talent', label: 'Talent Profiles' },
  { value: 'visual', label: 'Visual Workers' },
  { value: 'expressive', label: 'Expressive Workers' },
  { value: 'hybrid', label: 'Hybrid Workers' },
  { value: 'bands', label: 'Bands' },
  { value: 'background', label: 'Background Profiles' },
  { value: 'props', label: 'Props' },
  { value: 'costumes', label: 'Costumes' },
  { value: 'memorabilia', label: 'Memorabilia' },
  { value: 'vehicles', label: 'Vehicles' },
  { value: 'artistic_materials', label: 'Artistic Materials' },
  { value: 'music_items', label: 'Music Items' },
  { value: 'rare_items', label: 'Rare Items' },
];

const SearchBar: React.FC<SearchBarProps> = ({
  profileType,
  onProfileTypeChange,
  onSearch,
  onReset,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearch = () => {
    const searchParams: Partial<SearchParams> = {};
    
    if (searchTerm.trim()) {
      // Add search term based on profile type
      switch (profileType) {
        case 'talent':
          searchParams.city = searchTerm;
          break;
        case 'bands':
          searchParams.name = searchTerm;
          break;
        default:
          searchParams.name = searchTerm;
      }
    }
    
    onSearch(searchParams);
  };

  const handleReset = () => {
    setSearchTerm('');
    onReset();
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Profile Type</InputLabel>
          <Select
            value={profileType}
            label="Profile Type"
            onChange={(e) => onProfileTypeChange(e.target.value as ProfileType)}
          >
            {profileTypes.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                {type.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          label="Search"
          variant="outlined"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          sx={{ flex: 1 }}
          placeholder={`Search ${profileTypes.find(t => t.value === profileType)?.label.toLowerCase()}...`}
        />

        <Button
          variant="contained"
          startIcon={<Search />}
          onClick={handleSearch}
        >
          Search
        </Button>

        <Button
          variant="outlined"
          startIcon={<Clear />}
          onClick={handleReset}
        >
          Reset
        </Button>
      </Box>
    </Paper>
  );
};

export default SearchBar;
```

```tsx
// src/components/search/FilterPanel.tsx
import React from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Slider,
} from '@mui/material';
import { ProfileType, SearchParams } from '../../types/search.types';

interface FilterPanelProps {
  profileType: ProfileType;
  currentFilters: SearchParams;
  onFiltersChange: (filters: Partial<SearchParams>) => void;
}

const FilterPanel: React.FC<FilterPanelProps> = ({
  profileType,
  currentFilters,
  onFiltersChange,
}) => {
  const handleFilterChange = (key: string, value: any) => {
    onFiltersChange({ [key]: value });
  };

  const renderTalentFilters = () => (
    <>
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Gender</InputLabel>
        <Select
          value={currentFilters.gender || ''}
          label="Gender"
          onChange={(e) => handleFilterChange('gender', e.target.value)}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="Male">Male</MenuItem>
          <MenuItem value="Female">Female</MenuItem>
          <MenuItem value="Other">Other</MenuItem>
        </Select>
      </FormControl>

      <TextField
        fullWidth
        label="City"
        value={currentFilters.city || ''}
        onChange={(e) => handleFilterChange('city', e.target.value)}
        sx={{ mb: 2 }}
      />

      <TextField
        fullWidth
        label="Country"
        value={currentFilters.country || ''}
        onChange={(e) => handleFilterChange('country', e.target.value)}
        sx={{ mb: 2 }}
      />

      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Account Type</InputLabel>
        <Select
          value={currentFilters.account_type || ''}
          label="Account Type"
          onChange={(e) => handleFilterChange('account_type', e.target.value)}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="free">Free</MenuItem>
          <MenuItem value="silver">Silver</MenuItem>
          <MenuItem value="gold">Gold</MenuItem>
          <MenuItem value="platinum">Platinum</MenuItem>
        </Select>
      </FormControl>

      <FormControlLabel
        control={
          <Checkbox
            checked={currentFilters.is_verified || false}
            onChange={(e) => handleFilterChange('is_verified', e.target.checked)}
          />
        }
        label="Verified Only"
        sx={{ mb: 2 }}
      />

      <Box sx={{ mb: 2 }}>
        <Typography gutterBottom>Age</Typography>
        <Slider
          value={currentFilters.age || 25}
          onChange={(_, value) => handleFilterChange('age', value)}
          min={18}
          max={65}
          valueLabelDisplay="auto"
        />
      </Box>
    </>
  );

  const renderVisualWorkerFilters = () => (
    <>
      <TextField
        fullWidth
        label="Primary Category"
        value={currentFilters.primary_category || ''}
        onChange={(e) => handleFilterChange('primary_category', e.target.value)}
        sx={{ mb: 2 }}
      />

      <TextField
        fullWidth
        label="Experience Level"
        value={currentFilters.experience_level || ''}
        onChange={(e) => handleFilterChange('experience_level', e.target.value)}
        sx={{ mb: 2 }}
      />

      <Box sx={{ mb: 2 }}>
        <Typography gutterBottom>Years of Experience</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            label="Min"
            type="number"
            value={currentFilters.min_years_experience || ''}
            onChange={(e) => handleFilterChange('min_years_experience', parseInt(e.target.value) || undefined)}
            size="small"
          />
          <TextField
            label="Max"
            type="number"
            value={currentFilters.max_years_experience || ''}
            onChange={(e) => handleFilterChange('max_years_experience', parseInt(e.target.value) || undefined)}
            size="small"
          />
        </Box>
      </Box>

      <TextField
        fullWidth
        label="City"
        value={currentFilters.city || ''}
        onChange={(e) => handleFilterChange('city', e.target.value)}
        sx={{ mb: 2 }}
      />

      <TextField
        fullWidth
        label="Country"
        value={currentFilters.country || ''}
        onChange={(e) => handleFilterChange('country', e.target.value)}
        sx={{ mb: 2 }}
      />

      <FormControlLabel
        control={
          <Checkbox
            checked={currentFilters.willing_to_relocate || false}
            onChange={(e) => handleFilterChange('willing_to_relocate', e.target.checked)}
          />
        }
        label="Willing to Relocate"
        sx={{ mb: 2 }}
      />
    </>
  );

  const renderExpressiveWorkerFilters = () => (
    <>
      <TextField
        fullWidth
        label="Performer Type"
        value={currentFilters.performer_type || ''}
        onChange={(e) => handleFilterChange('performer_type', e.target.value)}
        sx={{ mb: 2 }}
      />

      <Box sx={{ mb: 2 }}>
        <Typography gutterBottom>Years of Experience</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            label="Min"
            type="number"
            value={currentFilters.min_years_experience || ''}
            onChange={(e) => handleFilterChange('min_years_experience', parseInt(e.target.value) || undefined)}
            size="small"
          />
          <TextField
            label="Max"
            type="number"
            value={currentFilters.max_years_experience || ''}
            onChange={(e) => handleFilterChange('max_years_experience', parseInt(e.target.value) || undefined)}
            size="small"
          />
        </Box>
      </Box>

      <TextField
        fullWidth
        label="Hair Color"
        value={currentFilters.hair_color || ''}
        onChange={(e) => handleFilterChange('hair_color', e.target.value)}
        sx={{ mb: 2 }}
      />

      <TextField
        fullWidth
        label="Eye Color"
        value={currentFilters.eye_color || ''}
        onChange={(e) => handleFilterChange('eye_color', e.target.value)}
        sx={{ mb: 2 }}
      />

      <TextField
        fullWidth
        label="Body Type"
        value={currentFilters.body_type || ''}
        onChange={(e) => handleFilterChange('body_type', e.target.value)}
        sx={{ mb: 2 }}
      />

      <Box sx={{ mb: 2 }}>
        <Typography gutterBottom>Physical Attributes</Typography>
        <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
          <TextField
            label="Height (cm)"
            type="number"
            value={currentFilters.height || ''}
            onChange={(e) => handleFilterChange('height', parseFloat(e.target.value) || undefined)}
            size="small"
          />
          <TextField
            label="Weight (kg)"
            type="number"
            value={currentFilters.weight || ''}
            onChange={(e) => handleFilterChange('weight', parseFloat(e.target.value) || undefined)}
            size="small"
          />
        </Box>
      </Box>
    </>
  );

  const renderBandFilters = () => (
    <>
      <TextField
        fullWidth
        label="Band Name"
        value={currentFilters.name || ''}
        onChange={(e) => handleFilterChange('name', e.target.value)}
        sx={{ mb: 2 }}
      />

      <TextField
        fullWidth
        label="Band Type"
        value={currentFilters.band_type || ''}
        onChange={(e) => handleFilterChange('band_type', e.target.value)}
        sx={{ mb: 2 }}
      />

      <TextField
        fullWidth
        label="Location"
        value={currentFilters.location || ''}
        onChange={(e) => handleFilterChange('location', e.target.value)}
        sx={{ mb: 2 }}
      />

      <Box sx={{ mb: 2 }}>
        <Typography gutterBottom>Number of Members</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            label="Min"
            type="number"
            value={currentFilters.min_members || ''}
            onChange={(e) => handleFilterChange('min_members', parseInt(e.target.value) || undefined)}
            size="small"
          />
          <TextField
            label="Max"
            type="number"
            value={currentFilters.max_members || ''}
            onChange={(e) => handleFilterChange('max_members', parseInt(e.target.value) || undefined)}
            size="small"
          />
        </Box>
      </Box>
    </>
  );

  const renderItemFilters = () => (
    <>
      <TextField
        fullWidth
        label="Name"
        value={currentFilters.name || ''}
        onChange={(e) => handleFilterChange('name', e.target.value)}
        sx={{ mb: 2 }}
      />

      <Box sx={{ mb: 2 }}>
        <Typography gutterBottom>Price Range</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            label="Min Price"
            type="number"
            value={currentFilters.min_price || ''}
            onChange={(e) => handleFilterChange('min_price', parseFloat(e.target.value) || undefined)}
            size="small"
          />
          <TextField
            label="Max Price"
            type="number"
            value={currentFilters.max_price || ''}
            onChange={(e) => handleFilterChange('max_price', parseFloat(e.target.value) || undefined)}
            size="small"
          />
        </Box>
      </Box>

      <FormControlLabel
        control={
          <Checkbox
            checked={currentFilters.is_for_rent || false}
            onChange={(e) => handleFilterChange('is_for_rent', e.target.checked)}
          />
        }
        label="Available for Rent"
        sx={{ mb: 1 }}
      />

      <FormControlLabel
        control={
          <Checkbox
            checked={currentFilters.is_for_sale || false}
            onChange={(e) => handleFilterChange('is_for_sale', e.target.checked)}
          />
        }
        label="Available for Sale"
        sx={{ mb: 2 }}
      />
    </>
  );

  const renderFilters = () => {
    switch (profileType) {
      case 'talent':
        return renderTalentFilters();
      case 'visual':
        return renderVisualWorkerFilters();
      case 'expressive':
        return renderExpressiveWorkerFilters();
      case 'bands':
        return renderBandFilters();
      case 'props':
      case 'costumes':
      case 'memorabilia':
      case 'vehicles':
      case 'artistic_materials':
      case 'music_items':
      case 'rare_items':
        return renderItemFilters();
      default:
        return <Typography>No filters available for this profile type.</Typography>;
    }
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Filters
      </Typography>
      {renderFilters()}
    </Paper>
  );
};

export default FilterPanel;
```

```tsx
// src/components/search/SearchResults.tsx
import React from 'react';
import {
  Box,
  Grid,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import { SearchResponse, ProfileType } from '../../types/search.types';
import ProfileCard from './ProfileCard';

interface SearchResultsProps {
  results: SearchResponse | null;
  loading: boolean;
  profileType: ProfileType;
}

const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  loading,
  profileType,
}) => {
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!results) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="text.secondary">
          Enter search criteria to find {profileType} profiles
        </Typography>
      </Box>
    );
  }

  if (results.results.length === 0) {
    return (
      <Alert severity="info">
        No {profileType} profiles found matching your search criteria.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Found {results.count} {profileType} profiles
      </Typography>
      
      <Grid container spacing={2}>
        {results.results.map((result) => (
          <Grid item xs={12} sm={6} md={4} key={result.id}>
            <ProfileCard
              profile={result}
              profileType={profileType}
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default SearchResults;
```

```tsx
// src/components/search/ProfileCard.tsx
import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  Avatar,
} from '@mui/material';
import { Person, Star, Visibility } from '@mui/icons-material';
import { SearchResult, ProfileType } from '../../types/search.types';

interface ProfileCardProps {
  profile: SearchResult;
  profileType: ProfileType;
}

const ProfileCard: React.FC<ProfileCardProps> = ({ profile, profileType }) => {
  const handleViewProfile = () => {
    // Navigate to profile details
    window.open(profile.profile_url, '_blank');
  };

  const renderProfileInfo = () => {
    switch (profileType) {
      case 'talent':
        return (
          <>
            <Typography variant="body2" color="text.secondary">
              {profile.city}, {profile.country}
            </Typography>
            <Typography variant="body2">
              Account: {profile.account_type}
            </Typography>
            {profile.is_verified && (
              <Chip label="Verified" color="primary" size="small" />
            )}
          </>
        );
      case 'visual':
        return (
          <>
            <Typography variant="body2" color="text.secondary">
              {profile.primary_category}
            </Typography>
            <Typography variant="body2">
              Experience: {profile.years_experience} years
            </Typography>
          </>
        );
      case 'expressive':
        return (
          <>
            <Typography variant="body2" color="text.secondary">
              {profile.performer_type}
            </Typography>
            <Typography variant="body2">
              {profile.height}cm, {profile.weight}kg
            </Typography>
          </>
        );
      case 'bands':
        return (
          <>
            <Typography variant="body2" color="text.secondary">
              {profile.band_type}
            </Typography>
            <Typography variant="body2">
              Members: {profile.member_count}
            </Typography>
          </>
        );
      default:
        return (
          <Typography variant="body2" color="text.secondary">
            {profile.description}
          </Typography>
        );
    }
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flex: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar sx={{ mr: 2 }}>
            <Person />
          </Avatar>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" component="h3">
              {profile.name || `${profileType} Profile`}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Star fontSize="small" color="primary" />
              <Typography variant="body2">
                Score: {profile.profile_score}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Relevance: {profile.relevance_score}
              </Typography>
            </Box>
          </Box>
        </Box>
        
        {renderProfileInfo()}
      </CardContent>
      
      <CardActions>
        <Button
          size="small"
          startIcon={<Visibility />}
          onClick={handleViewProfile}
          fullWidth
        >
          View Profile
        </Button>
      </CardActions>
    </Card>
  );
};

export default ProfileCard;
```

```tsx
// src/components/search/PaginationControls.tsx
import React from 'react';
import {
  Box,
  Button,
  Typography,
  Pagination,
} from '@mui/material';
import { NavigateBefore, NavigateNext } from '@mui/icons-material';

interface PaginationControlsProps {
  currentPage: number;
  totalCount: number;
  pageSize: number;
  hasNext: boolean;
  hasPrevious: boolean;
  onNextPage: () => void;
  onPreviousPage: () => void;
}

const PaginationControls: React.FC<PaginationControlsProps> = ({
  currentPage,
  totalCount,
  pageSize,
  hasNext,
  hasPrevious,
  onNextPage,
  onPreviousPage,
}) => {
  const totalPages = Math.ceil(totalCount / pageSize);
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalCount);

  return (
    <Box sx={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      mt: 3,
      p: 2,
      borderTop: 1,
      borderColor: 'divider'
    }}>
      <Typography variant="body2" color="text.secondary">
        Showing {startItem}-{endItem} of {totalCount} results
      </Typography>
      
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <Button
          variant="outlined"
          startIcon={<NavigateBefore />}
          onClick={onPreviousPage}
          disabled={!hasPrevious}
        >
          Previous
        </Button>
        
        <Typography variant="body2" sx={{ mx: 2 }}>
          Page {currentPage} of {totalPages}
        </Typography>
        
        <Button
          variant="outlined"
          endIcon={<NavigateNext />}
          onClick={onNextPage}
          disabled={!hasNext}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
};

export default PaginationControls;
```

## 6. Usage Example

```tsx
// src/App.tsx
import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import SearchContainer from './components/search/SearchContainer';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SearchContainer />
    </ThemeProvider>
  );
}

export default App;
```

## 7. Installation & Setup

```bash
# Install required dependencies
npm install @mui/material @emotion/react @emotion/styled
npm install @mui/icons-material
npm install axios
npm install @types/react @types/react-dom

# If using TypeScript
npm install typescript
```

## 8. Key Features Implemented

1. **Unified Search**: Single endpoint for all profile types
2. **Advanced Filtering**: Type-specific filters for each profile type
3. **Real-time Search**: Debounced search with loading states
4. **Pagination**: Full pagination support with next/previous controls
5. **Responsive Design**: Mobile-friendly Material-UI components
6. **Error Handling**: Comprehensive error handling and user feedback
7. **TypeScript Support**: Full type safety throughout the application
8. **Performance Optimized**: Debounced searches and efficient re-renders

## 9. Customization Options

- **Styling**: Customize Material-UI theme
- **Filters**: Add/remove filters based on requirements
- **Layout**: Modify grid layout and card designs
- **Search Logic**: Customize search parameters and debounce timing
- **Pagination**: Adjust page sizes and pagination controls

This implementation provides a complete, production-ready search interface that matches your backend API structure and includes all the necessary features for a professional talent management dashboard. 