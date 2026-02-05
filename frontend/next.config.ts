import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: false,
  // Note: We're running Next.js server in Electron, not using static export
  // This allows dynamic routes like /jobs/[id] to work properly
};

export default nextConfig;
