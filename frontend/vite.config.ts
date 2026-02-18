import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        host: true,
        strictPort: true,
        port: 5173,
        allowedHosts: true, // Permite cualquier host durante la demo/EC2
        watch: {
            usePolling: true
        },
        headers: {
            'Cross-Origin-Opener-Policy': 'same-origin-allow-popups'
        }
    }
})
