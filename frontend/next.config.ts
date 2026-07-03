import type { NextConfig } from 'next'
import withPWAInit from '@ducanh2912/next-pwa'

const nextConfig: NextConfig = {
  experimental: { typedRoutes: false },
}

const withPWA = withPWAInit({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development',
  cacheOnFrontEndNav: true,
  register: true,
  workboxOptions: {
    skipWaiting: true,
  },
})

export default withPWA(nextConfig)
