/**
 * Utilitários de máscara e validação para entradas brasileiras.
 *
 * Funções puras, sem efeitos colaterais, usadas por formulários e exibição.
 */

import { ufsValidas } from '../constants/dominio'

/**
 * Aplica máscara de telefone brasileiro a partir de dígitos.
 *
 * Aceita fixo (10 dígitos) e celular (11 dígitos), formatando progressivamente
 * conforme o usuário digita. Caracteres não numéricos são ignorados e o número
 * é truncado em 11 dígitos.
 *
 * @param valor - Texto digitado (pode conter máscara parcial).
 * @returns Telefone com máscara PT-BR (ex.: "(11) 99999-0000").
 */
export function formatarTelefone(valor: string): string {
  const digitos = valor.replace(/\D/g, '').slice(0, 11)
  if (digitos.length === 0) {
    return ''
  }
  if (digitos.length <= 2) {
    return `(${digitos}`
  }
  const ddd = digitos.slice(0, 2)
  const resto = digitos.slice(2)
  if (resto.length <= 4) {
    return `(${ddd}) ${resto}`
  }
  if (digitos.length <= 10) {
    return `(${ddd}) ${resto.slice(0, 4)}-${resto.slice(4)}`
  }
  return `(${ddd}) ${resto.slice(0, 5)}-${resto.slice(5)}`
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * Valida o formato de um e-mail.
 *
 * @param valor - E-mail informado.
 * @returns `true` quando o formato é plausível.
 */
export function isEmailValido(valor: string): boolean {
  return EMAIL_REGEX.test(valor.trim())
}

/**
 * Valida um telefone brasileiro (10 ou 11 dígitos).
 *
 * @param valor - Telefone informado (com ou sem máscara).
 * @returns `true` quando possui 10 ou 11 dígitos.
 */
export function isTelefoneValido(valor: string): boolean {
  const digitos = valor.replace(/\D/g, '')
  return digitos.length === 10 || digitos.length === 11
}

/**
 * Valida uma sigla de UF brasileira.
 *
 * @param valor - Sigla informada (ex.: "sp", "SP").
 * @returns `true` quando corresponde a uma UF real.
 */
export function isUfValida(valor: string): boolean {
  return ufsValidas.has(valor.trim().toUpperCase())
}
