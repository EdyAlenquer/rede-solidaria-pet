import '@testing-library/jest-dom'

function criarStorage(): Storage {
  const itens = new Map<string, string>()

  return {
    get length() {
      return itens.size
    },
    clear() {
      itens.clear()
    },
    getItem(chave: string) {
      return itens.get(chave) ?? null
    },
    key(indice: number) {
      return Array.from(itens.keys())[indice] ?? null
    },
    removeItem(chave: string) {
      itens.delete(chave)
    },
    setItem(chave: string, valor: string) {
      itens.set(chave, String(valor))
    },
  }
}

if (typeof globalThis.localStorage === 'undefined') {
  Object.defineProperty(globalThis, 'localStorage', {
    configurable: true,
    value: criarStorage(),
  })
}
