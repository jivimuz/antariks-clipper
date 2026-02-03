/**
 * Type definitions for license-related objects
 */

export interface LicenseStatus {
  licenseKey?: string;
  activated: boolean;
  valid?: boolean;
  owner?: string;
  expires?: string;
  error?: string;
  needs_validation?: boolean;
  daysRemaining?: number | null;
  expiringSoon?: boolean;
}

export interface LicenseActivationResponse {
  success: boolean;
  owner?: string;
  expires?: string;
  error?: string;
  detail?: string;  // For error responses from API
  daysRemaining?: number | null;
  expiringSoon?: boolean;
}
