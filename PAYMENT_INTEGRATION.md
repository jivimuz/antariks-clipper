# Payment Integration

## External Payment Processing

Payments for Antariks Clipper licenses are processed on a separate Antariks website (https://antariks.id).

## License Activation Flow

1. User purchases a license on the Antariks website
2. Payment is processed externally
3. User receives a license key via email or on the purchase confirmation page
4. User activates the license in the Antariks Clipper application using the `/license` activation page

## License Management

The application uses a license validation system that:
- Validates license keys against the Antariks license server
- Requires license activation before application usage
- Caches license validation for 24 hours
- Binds licenses to device MAC addresses for security

See the license activation page at `/license` in the application for more details.

