/**
 * Validation utilities for forms
 */

/**
 * Validate YouTube URL
 * @param url - The URL to validate
 * @returns true if valid YouTube URL, false otherwise
 */
export function isValidYouTubeUrl(url: string): boolean {
  if (!url || typeof url !== 'string') return false;
  
  // YouTube URL patterns - allow additional query parameters
  const patterns = [
    /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})(?:&.*)?$/,
    /^(https?:\/\/)?(www\.)?(youtu\.be\/)([a-zA-Z0-9_-]{11})(?:\?.*)?$/,
    /^(https?:\/\/)?(www\.)?(youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})(?:\?.*)?$/,
    /^(https?:\/\/)?(www\.)?(youtube\.com\/v\/)([a-zA-Z0-9_-]{11})(?:\?.*)?$/,
  ];
  
  return patterns.some(pattern => pattern.test(url));
}

/**
 * Validate video file
 * @param file - The file to validate
 * @param maxSizeInMB - Maximum file size in MB (default: 500MB)
 * @returns Object with isValid flag and error message if invalid
 */
export function validateVideoFile(
  file: File | null,
  maxSizeInMB: number = 500
): { isValid: boolean; error?: string } {
  if (!file) {
    return { isValid: false, error: 'No file selected' };
  }

  // Check file type
  const validTypes = ['video/mp4', 'video/quicktime', 'video/webm', 'video/x-matroska', 'video/avi'];
  if (!validTypes.includes(file.type)) {
    return { 
      isValid: false, 
      error: 'Invalid file type. Please upload MP4, MOV, WebM, MKV, or AVI files.' 
    };
  }

  // Check file size
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
  if (file.size > maxSizeInBytes) {
    return { 
      isValid: false, 
      error: `File size exceeds ${maxSizeInMB}MB limit. Please upload a smaller file.` 
    };
  }

  return { isValid: true };
}

/**
 * Format file size for display
 * @param bytes - File size in bytes
 * @returns Formatted string (e.g., "15.5 MB")
 */
export function formatFileSize(bytes: number): string {
  // Handle invalid inputs
  if (typeof bytes !== 'number' || bytes < 0 || !isFinite(bytes)) {
    return '0 Bytes';
  }
  
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}
