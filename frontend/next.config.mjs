/** @type {import('next').NextConfig} */
const apiOrigin = process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";
const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/api/:path*`,
      },
      {
        source: "/health",
        destination: `${apiOrigin}/health`,
      },
    ];
  },
};
export default nextConfig;
