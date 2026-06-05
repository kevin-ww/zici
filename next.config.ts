import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  async rewrites() {
    if (process.env.NEXT_PUBLIC_API_BASE_URL) {
      return []
    }

    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ]
  },
}

export default nextConfig
