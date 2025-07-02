/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker production builds
  output: 'standalone',
  
  // Configure image domains if you're using Next.js Image component
  images: {
    domains: [
      'figma-alpha-api.s3.us-west-2.amazonaws.com',
      'turbo-web-bucket.s3.amazonaws.com',
      'source.unsplash.com',
      'plus.unsplash.com',
      'images.unsplash.com',
      'localhost'
    ],
  },
  
  // Environment variables that should be available on the client side
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
  },
};

export default nextConfig;
