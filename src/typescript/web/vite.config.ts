import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from 'vite'
import commonjs from 'vite-plugin-commonjs';
import mkcert from 'vite-plugin-mkcert'
import { VitePWA } from 'vite-plugin-pwa'

// https://vitejs.dev/config/
export default defineConfig(({mode}) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    define: {
      'process.env.REACT_APP_AUTH_SERVER_URL': JSON.stringify(env.REACT_APP_AUTH_SERVER_URL),
      'process.env.REACT_APP_AUTH_REALM_NAME': JSON.stringify(env.REACT_APP_AUTH_REALM_NAME),
      'process.env.REACT_APP_AUTH_CLIENT_ID': JSON.stringify(env.REACT_APP_AUTH_CLIENT_ID),
      'process.env.REACT_APP_COREAPIS_SERVER_URL': JSON.stringify(env.REACT_APP_COREAPIS_SERVER_URL),
      'process.env.REACT_APP_MAPBOX_API_TOKEN': JSON.stringify(env.REACT_APP_MAPBOX_API_TOKEN),
      'process.env.REACT_APP_OBJECT_STORAGE_ENDPOINT': JSON.stringify(env.REACT_APP_OBJECT_STORAGE_ENDPOINT),
      'process.env.REACT_APP_MODELAPIS_SERVER_URL': JSON.stringify(env.REACT_APP_MODELAPIS_SERVER_URL),
    },
    plugins: [
      react(),
      commonjs(),
      mkcert(),
      VitePWA({
        registerType: 'autoUpdate',
        injectRegister: 'auto',
        workbox: {
          maximumFileSizeToCacheInBytes: 10 * 1024 * 1024,
        },
        includeAssets: [
          'apple-touch-icon.png',
          'favicon-96x96.png',
          'favicon.ico',
        ],
        manifest: {
          name: 'Tornatura',
          short_name: 'Tornatura',
          description: 'Tornatura web app',
          theme_color: '#1b4332',
          background_color: '#ffffff',
          display: 'standalone',
          start_url: '/',
          icons: [
            {
              src: '/web-app-manifest-192x192.png',
              sizes: '192x192',
              type: 'image/png',
            },
            {
              src: '/web-app-manifest-512x512.png',
              sizes: '512x512',
              type: 'image/png',
            },
          ],
        },
      }),
    ]
  }
});
