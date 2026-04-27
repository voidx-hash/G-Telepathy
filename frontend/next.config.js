/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker/self-hosted deployment
  // This bundles all dependencies into .next/standalone for a minimal image
  output: process.env.NEXT_BUILD_STANDALONE === "true" ? "standalone" : undefined,

  images: {
    remotePatterns: [
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
      { protocol: "https", hostname: "avatars.githubusercontent.com" },
      { protocol: "https", hostname: "*.supabase.co" },
    ],
  },
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
};

module.exports = nextConfig;
