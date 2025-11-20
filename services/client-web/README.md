# Qalb SMS Client Portal

Next.js 14 App Router client portal for the Qalb SMS platform.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **Form Handling**: React Hook Form + Zod
- **Icons**: Lucide React

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Visit http://localhost:3000

### Build

```bash
npm run build
npm start
```

## Project Structure

```
services/client-web/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── globals.css
│   ├── layout.tsx
│   ├── page.tsx
│   └── providers.tsx
├── components/
│   ├── auth/
│   │   ├── login-form.tsx
│   │   └── register-form.tsx
│   ├── dashboard/
│   │   ├── dashboard-header.tsx
│   │   ├── dashboard-nav.tsx
│   │   ├── dashboard-stats.tsx
│   │   └── recent-messages.tsx
│   └── ui/
│       ├── button.tsx
│       ├── card.tsx
│       ├── input.tsx
│       └── label.tsx
├── lib/
│   ├── api/
│   │   ├── auth.ts
│   │   └── client.ts
│   ├── stores/
│   │   └── auth-store.ts
│   └── utils.ts
├── types/
│   └── api.ts
├── .env.local
├── .eslintrc.json
├── .gitignore
├── components.json
├── next.config.mjs
├── package.json
├── postcss.config.mjs
├── tailwind.config.ts
└── tsconfig.json
```

## Environment Variables

Create a `.env.local` file:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
```

## Features

- **Authentication**: Login/Register with JWT
- **Dashboard**: Overview with stats and recent activity
- **Route Groups**: Organized auth and dashboard layouts
- **API Integration**: Axios client with interceptors
- **State Management**: Zustand for auth state persistence
- **Type Safety**: Full TypeScript coverage
- **Responsive Design**: Mobile-first with Tailwind CSS
- **Docker Ready**: Standalone output for containerization

## Docker Build

The project is configured with `output: 'standalone'` for optimized Docker builds:

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

## Code Style

- ESLint with Next.js recommended config
- TypeScript strict mode
- Tailwind CSS for styling
- Component-first architecture
- Hooks for state management

## License

Private - Qalb SMS Platform
