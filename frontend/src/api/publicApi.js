import {DEMO_MODE} from '../config';
import {request} from './client';
import {clinic,services as demoServices,staff as demoStaff} from '../data/demo';
const wait=(x)=>new Promise(r=>setTimeout(()=>r(structuredClone(x)),180));
const serviceImages=demoServices.map(x=>x.image);
const doctorImages=demoStaff.map(x=>x.image);
const normalizeService=(x,i=0)=>({
  ...x,
  price:Number(x.price_from??x.price??0),
  description:x.description||x.short_description||'',
  image:x.image||serviceImages[i%serviceImages.length]
});
const normalizeStaff=(x,i=0)=>({
  ...x,
  name:x.name||x.full_name,
  role:x.role||x.title||x.staff_type||'Aesthetic Doctor',
  image:x.image||doctorImages[i%doctorImages.length]
});
export const publicApi={
 getClinic:()=>DEMO_MODE?wait(clinic):request('/public/clinic'),
 getServices:async()=>DEMO_MODE?wait(demoServices):(await request('/public/services')).map(normalizeService),
 getStaff:async()=>DEMO_MODE?wait(demoStaff):(await request('/public/staff')).map(normalizeStaff),
 getAvailability:async({service_id,date,staff_id}={})=>{
   if(DEMO_MODE)return wait([{time:'10:00',staff_id:'st-1',staff_name:'dr. Alina Pratama',available:true},{time:'11:30',staff_id:'st-2',staff_name:'dr. Nadia Arum',available:true},{time:'14:00',staff_id:'st-3',staff_name:'dr. Keisha Mahendra',available:true},{time:'16:30',staff_id:'st-1',staff_name:'dr. Alina Pratama',available:true}]);
   const raw=await request(`/public/availability?service_id=${encodeURIComponent(service_id||'')}&date=${encodeURIComponent(date||'')}${staff_id?`&staff_id=${encodeURIComponent(staff_id)}`:''}`);
   return raw.map(x=>({...x,time:new Date(x.starts_at).toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit',hour12:false}).replace('.',':'),available:true}));
 },
 createAppointment:(payload)=>{
   if(DEMO_MODE)return wait({id:`req-${Date.now()}`,status:'requested',...payload});
   return request('/public/appointment-requests',{method:'POST',body:{
     full_name:payload.name||payload.full_name,
     phone:payload.phone,
     email:payload.email||null,
     service_id:payload.service_id,
     staff_id:payload.staff_id,
     starts_at:payload.starts_at||payload.scheduled_at,
     note:payload.note||null
   }});
 },
 createConversation:async()=>{
   if(DEMO_MODE)return wait({id:`conv-${Date.now()}`,token:'demo-public-token',status:'ai_active'});
   const x=await request('/public/conversations',{method:'POST'});
   return {id:x.conversation_id,token:x.conversation_token,status:x.status};
 },
 sendMessage:(conversation,payload)=>{
   if(DEMO_MODE)return wait({message:'Terima kasih. Saya Clevia AI — saya bisa bantu informasi treatment, jadwal dokter, atau booking. Untuk kebutuhan spesifik, saya akan mengarahkan ke tim klinik.',conversation_status:'ai_active',tools_used:[]});
   const id=typeof conversation==='string'?conversation:conversation.id;
   const token=typeof conversation==='object'?conversation.token:payload.conversation_token;
   return request(`/public/conversations/${id}/messages`,{method:'POST',body:{conversation_token:token,message:payload.message||payload.content}});
 }
};
