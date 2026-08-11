# Clevia Frontend

Frontend terpisah untuk Clevia Beauty Clinic: public multipage website, booking, web AI chatbot, admin login, dan CRM dashboard.

## Run
```bash
npm install
cp .env.example .env
npm run dev
```
Open `http://localhost:3000`.

## Demo login
`owner@clevia.local` / `ChangeMe123!`

## Live backend
Set:
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_DEMO_MODE=false
```
FastAPI CORS must allow `http://localhost:3000`.

## Routes
Public: `/`, `/about`, `/treatments`, `/doctors`, `/contact`, `/booking`.
CRM: `/admin/login`, `/admin`, `/admin/leads`, `/admin/clients`, `/admin/appointments`, `/admin/conversations`, `/admin/knowledge`, `/admin/settings`.

The current backend has no CRM endpoint to read a conversation transcript, so live mode shows conversation metadata plus takeover/release. Demo mode includes a sample transcript.

## Visual refresh v1.2.2
- White-first luxury interface with champagne and metallic-gold accents.
- Refined public landing pages, booking flow, login, and CRM surfaces.
- Redesigned Clevia AI Concierge widget with quick prompts and a cleaner composer.
- Local SVG icon set is used consistently; no lucide-react dependency is required.
