/**
 * Get the API URL from environment variables
 * @returns The API URL (defaults to http://localhost:8000 if not set)
 */
export function getApiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

/**
 * Build a full API endpoint URL
 * @param path - The API endpoint path (e.g., '/api/jobs')
 * @returns The full API URL
 */
export function getApiEndpoint(path: string): string {
  const baseUrl = getApiUrl();
  // Ensure path starts with /
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${cleanPath}`;
}
