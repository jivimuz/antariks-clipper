import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: false,
  // Enable static HTML export only for production build (Electron packaging)
  output: process.env.NODE_ENV === 'production' ? 'export' : undefined,
  distDir: 'out',
  // assetPrefix: process.env.NODE_ENV === 'production' ? './' : undefined,
  images: {
    unoptimized: true,
  },
  // Ensure API calls go to local backend
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:3211'
  }
};

export default nextConfig;
