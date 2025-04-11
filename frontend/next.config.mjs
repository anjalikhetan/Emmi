/** @type {import('next').NextConfig} */
const nextConfig = {
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
};

export default nextConfig;
