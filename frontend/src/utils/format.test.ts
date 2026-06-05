import { describe, expect, it } from 'vitest'

import {
  formatarTelefone,
  isEmailValido,
  isTelefoneValido,
  isUfValida,
} from './format'

describe('formatarTelefone', () => {
  it('formata celular com DDD (11 dígitos)', () => {
    expect(formatarTelefone('11999990000')).toBe('(11) 99999-0000')
  })

  it('formata fixo com DDD (10 dígitos)', () => {
    expect(formatarTelefone('1133334444')).toBe('(11) 3333-4444')
  })

  it('ignora caracteres não numéricos ao formatar', () => {
    expect(formatarTelefone('(11) 99999-0000')).toBe('(11) 99999-0000')
  })

  it('formata parcialmente enquanto o usuário digita', () => {
    expect(formatarTelefone('11')).toBe('(11')
    expect(formatarTelefone('119')).toBe('(11) 9')
  })

  it('limita a 11 dígitos', () => {
    expect(formatarTelefone('1199999000012345')).toBe('(11) 99999-0000')
  })
})

describe('isEmailValido', () => {
  it('aceita e-mails válidos', () => {
    expect(isEmailValido('maria@example.com')).toBe(true)
  })

  it('rejeita e-mails sem domínio ou arroba', () => {
    expect(isEmailValido('maria@')).toBe(false)
    expect(isEmailValido('maria.example.com')).toBe(false)
    expect(isEmailValido('')).toBe(false)
  })
})

describe('isTelefoneValido', () => {
  it('aceita telefones com 10 ou 11 dígitos', () => {
    expect(isTelefoneValido('11999990000')).toBe(true)
    expect(isTelefoneValido('(11) 3333-4444')).toBe(true)
  })

  it('rejeita telefones curtos demais', () => {
    expect(isTelefoneValido('99999')).toBe(false)
  })
})

describe('isUfValida', () => {
  it('aceita UFs reais sem diferenciar caixa', () => {
    expect(isUfValida('SP')).toBe(true)
    expect(isUfValida('sp')).toBe(true)
  })

  it('rejeita siglas inexistentes', () => {
    expect(isUfValida('XX')).toBe(false)
    expect(isUfValida('S')).toBe(false)
  })
})
