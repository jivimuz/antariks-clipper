/**
 * Get the API URL from environment variables
 * @returns The API URL (defaults to http://localhost:3211 if not set)
 */
export function getApiUrl(): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3211';
  console.log('[API] Using API URL:', apiUrl);
  return apiUrl;
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
