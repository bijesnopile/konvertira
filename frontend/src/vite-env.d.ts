/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_LOCAL_IMAGE_MAX_SIZE_MB?: string
  readonly VITE_LOCAL_IMAGE_MAX_PIXELS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
