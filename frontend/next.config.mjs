/** @type {import('next').NextConfig} */
const nextConfig = {
  trailingSlash: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*/",
        destination: "http://backend:8000/api/:path*/",
      },
    ];
  },
};

export default nextConfig;
