/**
 * Type definitions for license-related objects
 */

export interface LicenseStatus {
  activated: boolean;
  valid?: boolean;
  owner?: string;
  expires?: string;
  error?: string;
  needs_validation?: boolean;
}

export interface LicenseActivationResponse {
  success: boolean;
  owner?: string;
  expires?: string;
  error?: string;
  detail?: string;  // For error responses from API
}
