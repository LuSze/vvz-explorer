/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV === 'development';

const nextConfig = {
  // Only use standalone output in production
  output: isDev ? undefined : 'standalone',
  trailingSlash: true,
  // Use rewrites in both dev and prod, with correct service names
  async rewrites() {
    if (isDev) {
      return [
        {
          source: "/api/:path*/",
          destination: "http://backend:8000/api/:path*/",
        },
        {
          source: "/api/:path*",
          destination: "http://backend:8000/api/:path*",
        },
      ];
    }
    return [
      {
        source: "/api/:path*/",
        destination: "http://backend-prod:8000/api/:path*/",
      },
      {
        source: "/api/:path*",
        destination: "http://backend-prod:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
