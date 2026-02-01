/**
 * Frontend configuration
 * Uses environment variables with fallback to localhost for development
 */

export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
} as const;

// Validate configuration in development
if (process.env.NODE_ENV === 'development' && !process.env.NEXT_PUBLIC_API_URL) {
  console.warn('⚠️  NEXT_PUBLIC_API_URL not set, using default: http://localhost:8000');
}
