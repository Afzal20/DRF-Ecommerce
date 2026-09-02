# DRF-Ecommerce

A Django REST Framework e-commerce backend with **cookie-based JWT authentication** (including Google Sign-In), **Stripe Checkout** payments, and **AI-powered product tooling** via Groq. Designed to pair with a modern SPA / Next.js storefront.

## you can use it where you need 2 type of user. ( superuser and visitor)

![UI Screenshot](img/UI.png)

## Features

- **Authentication (httpOnly cookies)**
  - Email/password registration & login — JWT access/refresh tokens stored in secure cookies
  - Google Sign-In (`POST /accounts/user/google-login/` with an `id_token`)
  - JWT rotation & blacklist, short-lived access tokens
  - Email OTP flow for password reset (hashed OTP storage, single-use, constant-time verification)
  - Logout (cookie + token blacklist), token refresh/verify, password change, user profile
  - Scoped rate throttling for auth, OTP, and anonymous browsing
- **Shop**
  - Items with images, sizes, colors, variants, ratings, and vendor support (multi-vendor)
  - Categories, item types, districts, sliders, hero sections, coupons, refunds, contact messages
  - Per-user cart (create / list / update quantity / delete line items)
  - Orders & order items; Stripe Checkout session creation
  - Stripe webhook handler that marks orders paid and records payments
- **AI (Groq)**
  - Product description generator endpoint
  - Admin triage summary endpoint
- **Admin dashboard**
  - Payment tracking with related-order links, date drill-down, and search by email / charge ID
  - Order tracking with paid status, payment method, and Stripe transaction ID
- **API docs** — Swagger UI at `/docs/` (enabled when `DEBUG=True`)
- **Production hardening** — HSTS, SSL redirect, secure cookies, Swagger guard, whitenoise

## Tech Stack

| Layer | Tools |
|---|---|
| Framework | Django 6.1, Django REST Framework |
| Auth | djangorestframework-simplejwt (cookie transport), google-auth |
| Payments | Stripe (Checkout Sessions + webhooks) |
| AI | Groq API |
| Docs | drf-yasg (Swagger) |
| Tooling | uv (package manager), pre-commit (black, isort, ruff), pytest + factory_boy, GitHub Actions CI |

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)
- A Stripe account (test mode keys) — optional until you enable checkout
- A Groq API key — optional until you use the AI endpoints

### 1. Clone the project

```bash
git clone https://github.com/Afzal20/DRF_AUTH_with_Cookies.git
cd DRF_AUTH_with_Cookies
```

### 2. Install dependencies

```bash
uv sync
```

This creates a `.venv` and installs the runtime dependencies (dev/test tools are in dependency groups).

### 3. Configure environment variables

Copy the example file and fill in the values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | Secret key (no insecure fallback in production) |
| `STRIPE_PUBLIC_KEY` | For checkout | Stripe publishable key (`pk_test_...`) |
| `STRIPE_SECRET_KEY` | For checkout | Stripe secret key (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | For payments | Webhook signing secret (`whsec_...`) — see below |
| `GROQ_API_KEY` | For AI endpoints | Groq API key |

Email settings (for the OTP password-reset flow) live in `settings.py` — point them at your provider, or use the console backend in development:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### 4. Run migrations and create a superuser

```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

### 5. Start the dev server

```bash
uv run python manage.py runserver
```

- API: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- Swagger docs: `http://127.0.0.1:8000/docs/`

## API Overview

### Accounts (`/accounts/`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `user/register/` | Register a new user |
| POST | `user/login/` | Login (sets auth cookies) |
| POST | `user/google-login/` | Login with a Google `id_token` |
| GET/PATCH | `user/profile/` | View / update profile |
| POST | `password/change/` | Change password |
| POST | `token/refresh/` | Rotate refresh token |
| POST | `token/verify/`, `token/verify-access/` | Token verification |
| POST | `logout/` | Logout (clears cookies, blacklists token) |
| POST | `password-reset/request/` | Request OTP |
| POST | `password-reset/enterOtp/` | Verify OTP |
| POST | `password-reset/set_new_password/` | Set new password |

### Shop (`/shop/`)

| Method | Endpoint | Description |
|---|---|---|
| GET | `items/`, `items/<id>/` | Product catalog (with images, variants, absolute media URLs) |
| GET | `categories/`, `item-types/`, `sizes/`, `colors/`, `districts/`, ... | Reference data |
| GET/POST | `carts/` | List / add cart lines (authenticated, owner-scoped) |
| GET/PATCH/DELETE | `carts/<id>/` | Retrieve / update quantity / delete a cart line |
| GET/POST | `orders/`, `order-items/` | Orders and their items |
| POST | `stripe/create-checkout-session/` | Create a Stripe Checkout session for an order |
| POST | `stripe/webhook/` | Stripe webhook (marks order paid, records payment) |
| CRUD | `coupons/`, `refunds/`, `payments/`, `contacts/`, ... | Supporting resources |

### AI (`/api/v1/ai/`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `product-description/` | Generate a product description (Groq) |
| POST | `admin-triage/` | Admin triage summary (Groq) |

### AI Shopping Assistant (WebSocket)

`ws://127.0.0.1:8000/ws/ai/chat/` — a streaming shopping assistant powered by **OpenRouter** over **Django Channels**. Authentication (in order): the same `access_token` httpOnly cookie as the REST API, or a short-lived JWT via `?token=<jwt>` query param for cross-origin clients (the Next.js storefront does this via its `/api/ai/ws-token` route). Unauthenticated sockets are closed with code `4401`.

Protocol (JSON frames):

```
client -> {"type": "chat", "message": "...", "history": [{"role": "user"|"assistant", "content": "..."}]}
server <- {"type": "connected", "model": "...", "greeting": "..."}
server <- {"type": "start", "model": "..."}
server <- {"type": "token", "text": "..."}     (repeated, in order)
server <- {"type": "done"}
server <- {"type": "error", "message": "..."}
```

- Answers are grounded in the live product catalog (title, product_id, brand, price, stock, category).
- Model is configurable via `OPEN_ROUTER_MODEL` (default `google/gemma-4-31b-it:free`) with automatic fallback to other free models if one is rate-limited upstream.
- Every call is logged to `AICallLog` (provider `openrouter`) and visible in the Django admin.

Quick browser test (from any page on the API origin):

```js
const socket = new WebSocket("ws://127.0.0.1:8000/ws/ai/chat/");
socket.onmessage = (e) => console.log(JSON.parse(e.data));
socket.onopen = () =>
  socket.send(JSON.stringify({ type: "chat", message: "What lipsticks do you have?" }));
```


## Stripe Payments in Development

1. Put your `sk_test_...` key in `.env` and restart the server.
2. Checkout creates a session via `/shop/stripe/create-checkout-session/` and redirects the customer to Stripe.
3. **Payment records are created by the webhook**, so forward Stripe events to your local server:

   ```bash
   stripe login
   stripe listen --forward-to localhost:8000/shop/stripe/webhook/
   ```

   Copy the printed `whsec_...` into `.env` as `STRIPE_WEBHOOK_SECRET` and restart Django.

4. Pay with a test card:

   | Card | Result |
   |---|---|
   | `4242 4242 4242 4242` | ✅ Succeeds (any future expiry, any CVC) |
   | `4000 0025 0000 3155` | ✅ Succeeds after 3D Secure |
   | `4000 0000 0000 9995` | ❌ Declined (insufficient funds) |

   Full list: https://docs.stripe.com/testing

5. Verify in the admin: **Shop → Payments** shows the payment with a link to its order; **Shop → Orders** shows `ordered=True` and the Stripe transaction ID.

## Development

### Pre-commit hooks (black, isort, ruff)

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

### Tests

```bash
uv run pytest
```

### CI

A GitHub Actions pipeline (`.github/workflows/ci.yml`) runs linting, tests, and `pip-audit` on push.

## Architecture Decision Records

Design decisions are documented in `docs/adr/`:

1. `0001-vendor-model.md` — Vendor model & multi-vendor support
2. `0002-product-variants.md` — Product variants (sizes/colors)
3. `0003-ai-gateway.md` — AI gateway (Groq)
4. `0004-uuid-identifiers.md` — UUID identifiers
5. `0005-postgresql-migration.md` — PostgreSQL migration



## Recent Changes
- [x] Integrate AI Gateway (Groq) for dynamic text generation.
- [x] Create Product Description Generator endpoint.
- [x] Create Admin Triage Summary endpoint.
- [x] Google Sign-In endpoint (`/accounts/user/google-login/`) with `google-auth`.
- [x] Cart line-item detail endpoint (retrieve / update quantity / delete).
- [x] Stripe Checkout session creation with per-request API key and webhook handler for payments.
- [x] Absolute media URLs in serializers (cart/product images work from any origin).
- [x] Admin dashboard improvements: payment ↔ order tracking, date drill-down, email/charge-ID search.
- [x] Cookie-forwarding API proxy layer for the Next.js storefront (`/api/cart`, `/api/checkout`, `/api/auth/*`).
- [x] AI Shopping Assistant over WebSockets: Django Channels + OpenRouter with streaming, catalog grounding, and model fallback.
- Pinned dependencies and split requirements into base/dev/test (Phase 0 Step 1)
- Added pre-commit (ruff, black, isort) and fixed lint baseline (Phase 0 Step 2)
- Introduced pytest + factory_boy scaffolding with first smoke tests (Phase 0 Step 3)
- Added GitHub Actions CI pipeline with linting, testing, and pip-audit (Phase 0 Step 4)
- Hardened DEBUG and removed insecure SECRET_KEY fallback (Phase 0 Step 5)
- Created Architecture Decision Records (ADRs) directory and first five ADRs (Phase 0 Step 6)
- Enforced JWT rotation and blacklist, shortened token lifetimes (Phase 1 Step 7)
- Hashed OTP storage with constant-time verification and enforced single-use (Phase 1 Step 8)
- Added scoped rate throttling for auth, OTP, and anonymous browsing (Phase 1 Step 9)
- Hardened production settings: HSTS, SSL redirect, secure cookies, and Swagger guard (Phase 1 Step 10)
