/** @type {import('next').NextConfig} */
const nextConfig = {
  // Next dev serves the page over a LAN IP during the finalist presentation.
  // Keep the development asset/WebSocket origin explicit so Next does not
  // warn or block the browser when the host is not `localhost`.
  allowedDevOrigins: [
    'localhost',
    '127.0.0.1',
    '192.168.*.*',
    '10.*.*.*',
    // Next.js wildcard matching is segment based. Keep this aligned with
    // FastAPI's private 172.16/12 CORS range instead of using a recursive
    // wildcard that could match an unrelated hostname ending in ".172".
    '172.16.*.*',
    '172.17.*.*',
    '172.18.*.*',
    '172.19.*.*',
    '172.20.*.*',
    '172.21.*.*',
    '172.22.*.*',
    '172.23.*.*',
    '172.24.*.*',
    '172.25.*.*',
    '172.26.*.*',
    '172.27.*.*',
    '172.28.*.*',
    '172.29.*.*',
    '172.30.*.*',
    '172.31.*.*',
  ],
};
export default nextConfig;
