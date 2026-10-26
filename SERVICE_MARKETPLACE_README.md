<div align="center">

# Servify

**Open-source on-demand service marketplace engine with geospatial discovery, slot-level scheduling, and escrow payment settlement.**

[![CI](https://img.shields.io/github/actions/workflow/status/eswarprasadreddy/service-marketplace/ci.yml?branch=main&style=flat-square&label=CI&color=18181b)](https://github.com/eswarprasadreddy/service-marketplace/actions)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178c6?style=flat-square)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-18181b?style=flat-square)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostGIS-3.4-336791?style=flat-square)](https://postgis.net/)
[![Redis](https://img.shields.io/badge/Redis-7.2-dc2626?style=flat-square)](https://redis.io/)
[![License](https://img.shields.io/badge/license-MIT-71717a?style=flat-square)](LICENSE)

<p align="center">
  <a href="#overview">Overview</a> &bull;
  <a href="#architecture">Architecture</a> &bull;
  <a href="#booking--escrow-lifecycle">Booking Lifecycle</a> &bull;
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#data-models">Data Models</a> &bull;
  <a href="#api-reference">API Reference</a>
</p>

</div>

---

## Overview

Building multi-sided service marketplaces requires solving four difficult distributed systems problems simultaneously:

1. **Sub-second Geospatial Indexing**: Matching client locations with nearby verified professionals factoring in dynamic travel radiuses.
2. **Atomic Calendar Allocation**: Preventing double-bookings across concurrent requests with distributed locks and transit buffers.
3. **Escrow Protection**: Holding funds safely until client-verified job completion via cryptographic OTP or signature.
4. **Dispute Arbitration**: Maintaining an immutable audit log of job milestones, before/after media proofs, and in-app communications.

**Servify** provides an enterprise-ready, open-source foundation implementing these workflows out-of-the-box.

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Next.js 15 Client                    │
│     (App Router, React 19, Tailwind CSS, Shadcn UI)    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                   API Gateway & Auth                   │
│          (JWT / Role-Based Access Control)             │
└──────┬────────────────────┬────────────────────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Geospatial  │     │   Booking    │     │   Payments   │
│   Discovery  │     │State Machine │     │    Escrow    │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ PostgreSQL + │     │   Redis 7    │     │Stripe Connect│
│   PostGIS    │     │(Locks/PubSub)│     │Platform API  │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## Booking & Escrow Lifecycle

```
Client               API Gateway            Stripe Connect           Provider
  │                       │                       │                     │
  │── 1. Select Slot ────►│                       │                     │
  │                       │── 2. Acquire Redis ──►│                     │
  │                       │      Lock on Slot     │                     │
  │── 3. Authorize Pay ──►│                       │                     │
  │                       │── 4. Hold Escrow ────►│                     │
  │                       │      (PaymentIntent)  │                     │
  │                       │                       │                     │
  │                       │── 5. Dispatch Alert ───────────────────────►│
  │                       │                                             │
  │                       │   [ Service Execution & Job Delivery ]      │
  │                       │                                             │
  │── 6. Share 6-digit ────────────────────────────────────────────────►│
  │      Completion OTP   │                                             │
  │                       │◄─ 7. Submit OTP & Proof ────────────────────│
  │                       │                                             │
  │                       │── 8. Release Net Payout ───────────────────►│
  │                       │      (- Platform Take Rate)                 │
```

---

## Core Features

- **PostGIS Geospatial Discovery**: Sub-50ms radius queries using bounding box optimizations (`ST_DWithin`, `ST_MakePoint`).
- **Distributed Slot Reservation**: Atomic calendar locks implemented with Redis to prevent double bookings during checkout windows.
- **Two-Sided Escrow**: Full integration with Stripe Connect Custom/Express for multi-party splits, automated fee deduction, and payout release.
- **Real-Time Communication**: In-app WebSockets protocol for live provider tracking, messaging, and attachment uploads.
- **Job Proof Verification**: Enforces milestone completion with client-generated one-time passwords (OTP) and timestamped photo verification.

---

## Quick Start

### 1. Docker Compose (Recommended)

```bash
git clone https://github.com/eswarprasadreddy/service-marketplace.git
cd service-marketplace

# Configure environment
cp .env.example .env

# Start all services (PostgreSQL, PostGIS, Redis, API, Frontend)
docker compose up -d --build
```

- **Web Application**: [http://localhost:3000](http://localhost:3000)
- **API Documentation**: [http://localhost:4000/api/docs](http://localhost:4000/api/docs)

---

### 2. Manual Setup

#### Prerequisites
- Node.js 18+ or 20+
- PostgreSQL with `postgis` extension enabled
- Redis 7+
- Stripe CLI (for local webhook testing)

#### Backend

```bash
cd backend
npm install
cp .env.example .env

# Run database migrations and seed default categories
npx prisma migrate dev
npx prisma db seed

# Start server
npm run dev
```

#### Frontend

```bash
cd ../frontend
npm install
cp .env.example .env.local

npm run dev
```

---

## Data Models

Core entities defined via Prisma:

```prisma
enum Role {
  CLIENT
  PROVIDER
  ADMIN
}

enum BookingStatus {
  PENDING
  ACCEPTED
  IN_PROGRESS
  COMPLETED
  DISPUTED
  CANCELLED
}

model User {
  id              String           @id @default(uuid())
  email           String           @unique
  fullName        String
  role            Role             @default(CLIENT)
  providerProfile ProviderProfile?
  clientBookings  Booking[]        @relation("ClientBookings")
  createdAt       DateTime         @default(now())
}

model ProviderProfile {
  id              String        @id @default(uuid())
  userId          String        @unique
  user            User          @relation(fields: [userId], references: [id])
  serviceRadiusKm Float         @default(25.0)
  latitude        Float
  longitude       Float
  hourlyRate      Decimal       @db.Decimal(10, 2)
  isVerified      Boolean       @default(false)
  stripeAccountId String?
  bookings        Booking[]     @relation("ProviderBookings")
}

model Booking {
  id              String        @id @default(uuid())
  clientId        String
  providerId      String
  status          BookingStatus @default(PENDING)
  scheduledStart  DateTime
  scheduledEnd    DateTime
  totalAmount     Decimal       @db.Decimal(10, 2)
  escrowHoldId    String?
  completionOtp   String?
  client          User          @relation("ClientBookings", fields: [clientId], references: [id])
  provider        ProviderProfile @relation("ProviderBookings", fields: [providerId], references: [id])
  createdAt       DateTime      @default(now())
}
```

---

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/services/search` | Spatial radius search (`lat`, `lng`, `radiusKm`, `category`). |
| `POST` | `/api/v1/bookings/reserve` | Acquires temporary Redis lock on slot and creates draft booking. |
| `POST` | `/api/v1/payments/intent` | Generates Stripe Escrow PaymentIntent. |
| `POST` | `/api/v1/bookings/{id}/verify` | Validates client completion OTP and triggers escrow release. |
| `POST` | `/api/v1/disputes/create` | Freezes transaction funds and opens evidence docket. |
| `GET` | `/api/v1/providers/payouts` | Payout history and upcoming earnings. |

---

## Testing

```bash
# Run unit and integration tests
npm run test

# Run end-to-end booking flow test
npm run test:e2e
```

---

## License

This project is licensed under the [MIT License](LICENSE).
