"""Constantes de cache HTTP para respostas públicas compartilhadas."""

#: `Cache-Control` aplicado às leituras públicas e majoritariamente compartilhadas
#: (listagem de pedidos e estatísticas). O `public` permite cache em proxies/CDN e
#: o `max-age=30` mantém a janela curta o suficiente para não servir dados muito
#: desatualizados. NÃO deve ser usado em rotas autenticadas ou com dados por usuário.
CACHE_CONTROL_PUBLICO = "public, max-age=30"
