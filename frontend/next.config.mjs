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
    '172.**',
  ],
};
export default nextConfig;
