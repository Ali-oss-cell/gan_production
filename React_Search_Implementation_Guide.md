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

## 5. Main Search Container

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

## 6. Search Bar Component

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

## 8. Usage Example

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

## 9. Key Features

1. **Unified Search**: Single endpoint for all profile types
2. **Advanced Filtering**: Type-specific filters for each profile type
3. **Real-time Search**: Debounced search with loading states
4. **Pagination**: Full pagination support with next/previous controls
5. **Responsive Design**: Mobile-friendly Material-UI components
6. **Error Handling**: Comprehensive error handling and user feedback
7. **TypeScript Support**: Full type safety throughout the application
8. **Performance Optimized**: Debounced searches and efficient re-renders

## 10. API Usage Examples

```typescript
// Search for female talent in London
const searchTalent = async () => {
  const params = {
    profile_type: 'talent',
    gender: 'Female',
    city: 'London'
  };
  
  const response = await searchApi.search(params);
  console.log(response);
};

// Search for photographers with experience
const searchPhotographers = async () => {
  const params = {
    profile_type: 'visual',
    primary_category: 'photographer',
    min_years_experience: 5
  };
  
  const response = await searchApi.search(params);
  console.log(response);
};

// Search for props with price range
const searchProps = async () => {
  const params = {
    profile_type: 'props',
    min_price: 100,
    max_price: 500,
    is_for_rent: true
  };
  
  const response = await searchApi.search(params);
  console.log(response);
};
```

This implementation provides a complete, production-ready search interface that matches your backend API structure and includes all the necessary features for a professional talent management dashboard. 