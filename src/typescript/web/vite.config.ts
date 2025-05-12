import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from 'vite'
import commonjs from 'vite-plugin-commonjs';


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
    },
    plugins: [react(), commonjs()]
  }
});