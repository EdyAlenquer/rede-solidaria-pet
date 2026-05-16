# Frontend — Rede Solidária Pet

SPA construída com React + Vite + TypeScript.

## Requisitos

- Node 20+
- npm 10+

## Setup

```bash
cd frontend
npm install
cp .env.example .env
```

## Executar em desenvolvimento

```bash
npm run dev
```

A aplicação sobe em http://localhost:5173.

## Testes

```bash
npm run test
```

Modo watch:

```bash
npm run test:watch
```

## Build de produção

```bash
npm run build
npm run preview
```

## Lint e formatação

```bash
npm run lint
npm run format
```

## Estrutura

```
src/
├─ App.tsx              # componente raiz
├─ main.tsx             # bootstrap React
├─ pages/               # páginas (Fase 6)
├─ components/          # componentes reutilizáveis (Fase 5/6)
├─ hooks/               # hooks customizados
├─ services/api/        # cliente HTTP e endpoints (Fase 5)
├─ types/               # tipos TypeScript do domínio
├─ styles/              # estilos globais
└─ utils/               # utilidades puras
```
