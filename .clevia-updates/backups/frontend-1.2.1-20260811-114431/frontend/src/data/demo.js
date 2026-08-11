export const clinic={id:'clinic-1',name:'Clevia Beauty Clinic',tagline:'Confidence, refined.',description:'Klinik kecantikan modern yang memadukan pendekatan medis, personalisasi, dan pengalaman perawatan yang tenang.',phone:'+62 21 5550 2026',email:'hello@clevia.example',address:'Jakarta, Indonesia',instagram:'@cleviabeauty'};
export const services=[
{id:'srv-1',name:'Glow Facial Signature',category:'Facial',duration_minutes:60,price:650000,description:'Deep cleansing, gentle exfoliation, hydration, dan finishing glow untuk kulit tampak sehat.',image:'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?auto=format&fit=crop&w=1200&q=85'},
{id:'srv-2',name:'Acne Care Consultation',category:'Skin Health',duration_minutes:45,price:350000,description:'Konsultasi terarah untuk memahami kondisi acne dan menyusun rencana treatment yang realistis.',image:'https://images.unsplash.com/photo-1616394584738-fc6e612e71b9?auto=format&fit=crop&w=1200&q=85'},
{id:'srv-3',name:'Laser Rejuvenation',category:'Laser',duration_minutes:60,price:1500000,description:'Treatment berbasis energi untuk membantu tekstur kulit, tone, dan tampilan kulit lebih refined.',image:'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=1200&q=85'},
{id:'srv-4',name:'Skin Booster',category:'Injectable',duration_minutes:45,price:1850000,description:'Program hidrasi intensif dengan assessment dokter untuk kebutuhan kulit yang lebih spesifik.',image:'https://images.unsplash.com/photo-1515377905703-c4788e51af15?auto=format&fit=crop&w=1200&q=85'},
{id:'srv-5',name:'Brightening Peel',category:'Peel',duration_minutes:40,price:775000,description:'Chemical peel terukur untuk membantu kulit kusam dan uneven tone sesuai asesmen klinis.',image:'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=1200&q=85'},
{id:'srv-6',name:'Contour Consultation',category:'Consultation',duration_minutes:30,price:300000,description:'Konsultasi estetika wajah dengan pendekatan proporsi natural dan treatment plan bertahap.',image:'https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?auto=format&fit=crop&w=1200&q=85'}
];
export const staff=[
{id:'st-1',name:'dr. Alina Pratama',role:'Aesthetic Doctor',specialty:'Aesthetic Medicine',bio:'Berfokus pada skin health dan hasil estetika yang natural serta terukur.',image:'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=900&q=85'},
{id:'st-2',name:'dr. Nadia Arum',role:'Aesthetic Doctor',specialty:'Skin Rejuvenation',bio:'Menyusun treatment plan bertahap dengan prioritas pada keamanan dan skin barrier.',image:'https://images.unsplash.com/photo-1594824476967-48c8b964273f?auto=format&fit=crop&w=900&q=85'},
{id:'st-3',name:'dr. Keisha Mahendra',role:'Aesthetic Doctor',specialty:'Laser & Acne Care',bio:'Berfokus pada acne management dan laser-based rejuvenation.',image:'https://images.unsplash.com/photo-1666887361002-a6e4b10eb4eb?auto=format&fit=crop&w=900&q=85'}
];
export const leads=[
{id:'lead-1',name:'Maya Putri',phone:'0812 9932 1102',source:'Web Chat',interest:'Glow Facial',status:'new',created_at:'2026-08-10T09:15:00+07:00'},
{id:'lead-2',name:'Tania Lestari',phone:'0813 4410 2211',source:'WhatsApp',interest:'Laser Rejuvenation',status:'contacted',created_at:'2026-08-10T08:22:00+07:00'},
{id:'lead-3',name:'Raisa Anindya',phone:'0857 1112 9921',source:'Instagram',interest:'Skin Booster',status:'qualified',created_at:'2026-08-09T17:42:00+07:00'}
];
export const clients=[
{id:'cli-1',name:'Alya Rahma',phone:'0812 7711 2001',email:'alya@example.com',last_visit:'2026-08-06',visits:7},
{id:'cli-2',name:'Nina Sari',phone:'0813 9212 7400',email:'nina@example.com',last_visit:'2026-08-02',visits:4},
{id:'cli-3',name:'Cynthia Bella',phone:'0856 7201 9922',email:'cynthia@example.com',last_visit:'2026-07-29',visits:11}
];
export const appointments=[
{id:'apt-1',client_name:'Alya Rahma',service_name:'Glow Facial Signature',staff_name:'dr. Alina Pratama',scheduled_at:'2026-08-10T10:00:00+07:00',status:'confirmed'},
{id:'apt-2',client_name:'Nina Sari',service_name:'Laser Rejuvenation',staff_name:'dr. Nadia Arum',scheduled_at:'2026-08-10T11:30:00+07:00',status:'requested'},
{id:'apt-3',client_name:'Cynthia Bella',service_name:'Skin Booster',staff_name:'dr. Keisha Mahendra',scheduled_at:'2026-08-10T14:00:00+07:00',status:'confirmed'},
{id:'apt-4',client_name:'Tania Lestari',service_name:'Acne Care Consultation',staff_name:'dr. Alina Pratama',scheduled_at:'2026-08-10T16:00:00+07:00',status:'completed'}
];
export const conversations=[
{id:'conv-1',visitor_name:'Maya Putri',channel:'web',status:'ai_active',last_message:'Bisa cek jadwal facial untuk besok?',updated_at:'2026-08-10T10:08:00+07:00'},
{id:'conv-2',visitor_name:'Tania Lestari',channel:'whatsapp',status:'waiting_human',last_message:'Saya mau bicara dengan admin ya.',updated_at:'2026-08-10T09:51:00+07:00'},
{id:'conv-3',visitor_name:'Raisa Anindya',channel:'web',status:'human_active',last_message:'Baik kak, saya bantu cek ulang.',updated_at:'2026-08-10T09:16:00+07:00'}
];
export const messages={
'conv-1':[{role:'assistant',content:'Halo, saya Clevia AI. Ada yang bisa saya bantu?'},{role:'user',content:'Bisa cek jadwal facial untuk besok?'},{role:'assistant',content:'Tentu. Saya bisa bantu cek slot Glow Facial Signature. Anda lebih nyaman pagi atau sore?'}],
'conv-2':[{role:'user',content:'Saya tertarik laser, tapi mau tanya downtime.'},{role:'assistant',content:'Saya bisa jelaskan informasi umum dan bantu jadwalkan konsultasi dokter.'},{role:'user',content:'Saya mau bicara dengan admin ya.'}],
'conv-3':[{role:'user',content:'Booking saya tadi jam berapa?'},{role:'assistant',content:'Saya alihkan ke tim klinik agar data booking Anda dapat diverifikasi.'},{role:'staff',content:'Baik kak, saya bantu cek ulang.'}]};
export const knowledge=[
{id:'kb-1',title:'Jam Operasional Klinik',category:'Clinic Info',status:'published',updated_at:'2026-08-08',content:'Senin–Sabtu 09.00–20.00, Minggu dengan appointment.'},
{id:'kb-2',title:'Persiapan Laser Rejuvenation',category:'Treatment',status:'published',updated_at:'2026-08-07',content:'Hindari active ingredients tertentu sesuai arahan dokter dan gunakan sunscreen.'},
{id:'kb-3',title:'Kebijakan Reschedule',category:'Policy',status:'draft',updated_at:'2026-08-06',content:'Permintaan perubahan jadwal mengikuti ketersediaan slot klinik.'}
];
