# Backend Compatibility Notes

Frontend ini dibuat terpisah dan backend `/Clevia` tidak dimodifikasi.

## Endpoint yang sudah dipetakan

### Public
- `GET /api/v1/public/clinic`
- `GET /api/v1/public/services`
- `GET /api/v1/public/staff`
- `GET /api/v1/public/availability?service_id=&date=&staff_id=`
- `POST /api/v1/public/appointment-requests`
- `POST /api/v1/public/conversations`
- `POST /api/v1/public/conversations/{conversation_id}/messages`

Adapter frontend sudah menangani perbedaan nama field backend seperti:
- `price_from` -> `price`
- `full_name` -> `name`
- `conversation_id`/`conversation_token` -> state chat frontend
- `starts_at` -> tampilan waktu appointment

### CRM
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/crm/leads`
- `GET /api/v1/crm/clients`
- `GET /api/v1/appointments`
- `GET /api/v1/conversations`
- `POST /api/v1/conversations/{id}/takeover`
- `POST /api/v1/conversations/{id}/release`
- `GET /api/v1/knowledge`
- `POST /api/v1/knowledge`
- `POST /api/v1/knowledge/{id}/publish`

## Gap backend yang sengaja tidak dipalsukan oleh FE

Backend yang diaudit belum memiliki endpoint CRM untuk:
1. mengambil transcript/messages sebuah conversation;
2. mengirim balasan human agent melalui CRM;
3. preview `last_message` langsung dari conversation list;
4. aggregate analytics/revenue khusus dashboard.

Karena itu dashboard menggunakan demo data untuk visualisasi fitur tersebut saat `VITE_DEMO_MODE=true`. Pada Live Mode, Conversation UI menampilkan informasi gap secara eksplisit dan tidak mengarang response backend.
