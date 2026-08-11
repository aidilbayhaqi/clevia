import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'
export default defineConfig({
  esbuild:{jsx:'automatic'},
  resolve:{alias:{'lucide-react':fileURLToPath(new URL('./src/icons.jsx',import.meta.url))}},
  server:{port:3000,host:true}
})
