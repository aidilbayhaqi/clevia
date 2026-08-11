# Project Structure

```text
Clevia_FE/
├── src/
│   ├── api/                 # Adapter FastAPI + Demo Mode
│   ├── components/          # Public, auth, CRM layout components
│   ├── context/             # Auth state
│   ├── data/                # Demo-only presentation data
│   ├── pages/
│   │   ├── public/          # Multipage clinic website
│   │   └── admin/           # CRM screens
│   ├── styles/              # Global responsive design system
│   ├── utils/
│   ├── App.jsx
│   ├── icons.jsx            # Local SVG icon set, no icon dependency
│   └── main.jsx
├── .env.example
├── BACKEND_COMPATIBILITY.md
├── README.md
├── package.json
└── vite.config.js
```

## Route map

Public: `/`, `/treatments`, `/doctors`, `/about`, `/contact`, `/booking`

Admin: `/admin/login`, `/admin`, `/admin/leads`, `/admin/clients`, `/admin/appointments`, `/admin/conversations`, `/admin/knowledge`, `/admin/settings`
