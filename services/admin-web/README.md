# Admin Web - SMS Platform Admin Dashboard

Next.js 14 admin dashboard for the SMS platform with modern UI and real-time monitoring.

## Tech Stack

- **Next.js 14** - App Router, Server Components
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Zustand** - State management
- **TanStack Query** - Data fetching
- **Axios** - HTTP client
- **React Hook Form + Zod** - Form validation

## Getting Started

### Install Dependencies

```bash
npm install
```

### Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
```

### Development

```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000)

### Build

```bash
npm run build
npm start
```

## Project Structure

```
app/
├── (auth)/
│   └── login/         # Login page
├── (admin)/
│   ├── layout.tsx     # Admin layout with sidebar
│   ├── dashboard/     # Dashboard overview
│   ├── accounts/      # User account management
│   ├── operators/     # SMPP operator management
│   └── moderation/    # Content moderation
├── globals.css        # Global styles
├── layout.tsx         # Root layout
└── providers.tsx      # React Query provider

components/
└── ui/                # shadcn/ui components

lib/
├── api/
│   ├── client.ts      # Axios client with interceptors
│   └── admin.ts       # Admin API methods
├── stores/
│   └── auth-store.ts  # Zustand auth state
└── utils.ts           # Utility functions

types/
└── api.ts             # TypeScript type definitions
```

## Features

- Authentication with JWT
- Protected admin routes
- Responsive sidebar navigation
- Dashboard with stats
- Account management
- Operator management
- Content moderation
- Type-safe API client
- Form validation

## Docker

Build standalone:

```bash
npm run build
```

The standalone output will be in `.next/standalone/`

## License

Proprietary
