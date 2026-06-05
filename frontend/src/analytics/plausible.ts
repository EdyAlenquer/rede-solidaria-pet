/**
 * Analytics privacy-first via Plausible, ativada apenas por opt-in.
 *
 * O Plausible não usa cookies nem coleta dados pessoais, o que o mantém
 * compatível com a LGPD sem exigir banner de consentimento. Ainda assim, o
 * tracking só é carregado quando o domínio é explicitamente configurado em
 * `VITE_PLAUSIBLE_DOMAIN`; sem essa variável, nada é injetado.
 */

/** Id do elemento `<script>` injetado, usado para evitar duplicação. */
export const SCRIPT_ID = 'plausible-analytics'

/** Origem oficial do script do Plausible Analytics. */
const PLAUSIBLE_SRC = 'https://plausible.io/js/script.js'

/**
 * Injeta o script do Plausible no `<head>`, se configurado.
 *
 * Não faz nada quando `VITE_PLAUSIBLE_DOMAIN` está ausente/vazio (default, sem
 * tracking) ou quando o script já foi injetado anteriormente (idempotente).
 *
 * Side Effects:
 *   Adiciona um `<script defer>` em `document.head` quando o domínio está
 *   configurado e o script ainda não existe.
 */
export function injetarPlausible(): void {
  const dominio = import.meta.env.VITE_PLAUSIBLE_DOMAIN?.trim()
  if (!dominio) {
    return
  }
  if (document.getElementById(SCRIPT_ID)) {
    return
  }
  const script = document.createElement('script')
  script.id = SCRIPT_ID
  script.defer = true
  script.src = PLAUSIBLE_SRC
  script.setAttribute('data-domain', dominio)
  document.head.appendChild(script)
}
