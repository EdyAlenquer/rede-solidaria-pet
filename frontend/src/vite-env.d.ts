/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL pública da API do backend (ex.: https://.../api/v1). */
  readonly VITE_API_BASE_URL?: string
  /** Domínio registrado no Plausible; quando definido, ativa o analytics. */
  readonly VITE_PLAUSIBLE_DOMAIN?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
