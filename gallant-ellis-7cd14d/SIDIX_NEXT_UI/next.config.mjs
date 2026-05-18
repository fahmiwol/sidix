/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Backend FastAPI tetap di ctrl.sidixlab.com:8765 (tidak berubah).
  // Optional: rewrite /api/* ke backend untuk hindari CORS di dev.
  async rewrites() {
    const backend = process.env.NEXT_PUBLIC_BRAIN_QA_URL || 'https://ctrl.sidixlab.com';
    return [
      {
        source: '/api/brain/:path*',
        destination: `${backend}/:path*`,
      },
    ];
  },
};

export default nextConfig;
