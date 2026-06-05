import { afterEach, describe, expect, it, vi } from 'vitest'

import { injetarPlausible, SCRIPT_ID } from './plausible'

describe('injetarPlausible', () => {
  afterEach(() => {
    document.getElementById(SCRIPT_ID)?.remove()
    vi.unstubAllEnvs()
  })

  it('não injeta o script quando VITE_PLAUSIBLE_DOMAIN está ausente', () => {
    vi.stubEnv('VITE_PLAUSIBLE_DOMAIN', '')

    injetarPlausible()

    expect(document.getElementById(SCRIPT_ID)).toBeNull()
  })

  it('injeta o script do Plausible quando VITE_PLAUSIBLE_DOMAIN está definido', () => {
    vi.stubEnv('VITE_PLAUSIBLE_DOMAIN', 'redesolidariapet.org')

    injetarPlausible()

    const script = document.getElementById(SCRIPT_ID) as HTMLScriptElement | null
    expect(script).not.toBeNull()
    expect(script?.getAttribute('data-domain')).toBe('redesolidariapet.org')
    expect(script?.getAttribute('src')).toBe('https://plausible.io/js/script.js')
    expect(script?.defer).toBe(true)
  })

  it('não duplica o script em chamadas repetidas', () => {
    vi.stubEnv('VITE_PLAUSIBLE_DOMAIN', 'redesolidariapet.org')

    injetarPlausible()
    injetarPlausible()

    expect(document.querySelectorAll(`#${SCRIPT_ID}`)).toHaveLength(1)
  })
})
