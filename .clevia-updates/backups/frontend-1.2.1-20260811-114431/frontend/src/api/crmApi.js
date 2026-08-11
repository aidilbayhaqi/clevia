import {DEMO_MODE,TOKEN_KEY} from '../config';
import {request} from './client';
import {leads as demoLeads,clients as demoClients,appointments as demoAppointments,conversations as demoConversations,knowledge as demoKnowledge,messages} from '../data/demo';
const wait=(x)=>new Promise(r=>setTimeout(()=>r(structuredClone(x)),160));
const demoUser={id:'usr-1',name:'Clevia Owner',full_name:'Clevia Owner',email:'owner@clevia.local',role:'owner'};
const normalizeUser=x=>({...x,name:x.name||x.full_name});
export const crmApi={
 async login(email,password){
   if(DEMO_MODE){if(email!=='owner@clevia.local'||password!=='ChangeMe123!')throw new Error('Email atau password demo tidak sesuai.');const token='demo-clevia-token';localStorage.setItem(TOKEN_KEY,token);return wait({access_token:token,token_type:'bearer',user:demoUser});}
   const d=await request('/auth/login',{method:'POST',body:{email,password}});localStorage.setItem(TOKEN_KEY,d.access_token);return {...d,user:normalizeUser(d.user)};
 },
 async me(){return DEMO_MODE?wait(demoUser):normalizeUser(await request('/auth/me',{auth:true}))},
 async leads(){
   if(DEMO_MODE)return wait(demoLeads);
   const [rows,services]=await Promise.all([request('/crm/leads',{auth:true}),request('/public/services')]);
   const sm=new Map(services.map(s=>[s.id,s.name]));
   return rows.map(x=>({...x,name:x.full_name,interest:sm.get(x.interest_service_id)||'—'}));
 },
 async clients(){
   if(DEMO_MODE)return wait(demoClients);
   const rows=await request('/crm/clients',{auth:true});
   return rows.map(x=>({...x,name:x.full_name,last_visit:x.created_at,visits:0}));
 },
 async appointments(){
   if(DEMO_MODE)return wait(demoAppointments);
   const [rows,clients,leads,services,staff]=await Promise.all([
     request('/appointments',{auth:true}),request('/crm/clients',{auth:true}),request('/crm/leads',{auth:true}),request('/public/services'),request('/public/staff')
   ]);
   const cm=new Map(clients.map(x=>[x.id,x.full_name])),lm=new Map(leads.map(x=>[x.id,x.full_name])),sm=new Map(services.map(x=>[x.id,x.name])),dm=new Map(staff.map(x=>[x.id,x.full_name]));
   return rows.map(x=>({...x,client_name:cm.get(x.client_id)||lm.get(x.lead_id)||'Unlinked client',service_name:sm.get(x.service_id)||x.service_id,staff_name:dm.get(x.staff_id)||x.staff_id,scheduled_at:x.starts_at}));
 },
 async conversations(){
   if(DEMO_MODE)return wait(demoConversations);
   const [rows,clients,leads]=await Promise.all([request('/conversations',{auth:true}),request('/crm/clients',{auth:true}),request('/crm/leads',{auth:true})]);
   const cm=new Map(clients.map(x=>[x.id,x.full_name])),lm=new Map(leads.map(x=>[x.id,x.full_name]));
   return rows.map(x=>({...x,visitor_name:cm.get(x.client_id)||lm.get(x.lead_id)||`Visitor ${String(x.id).slice(0,6)}`,last_message:'Message preview unavailable in current API',updated_at:x.created_at}));
 },
 transcript:(id)=>DEMO_MODE?wait(messages[id]||[]):Promise.reject(new Error('Endpoint transcript/messages CRM belum tersedia pada backend yang diaudit.')),
 knowledge:()=>DEMO_MODE?wait(demoKnowledge):request('/knowledge',{auth:true}),
 takeover:(id)=>DEMO_MODE?wait({id,status:'human_active'}):request(`/conversations/${id}/takeover`,{method:'POST',auth:true}),
 release:(id)=>DEMO_MODE?wait({id,status:'ai_active'}):request(`/conversations/${id}/release`,{method:'POST',auth:true}),
 createKnowledge:(body)=>DEMO_MODE?wait({id:`kb-${Date.now()}`,status:'draft',...body}):request('/knowledge',{method:'POST',body,auth:true}),
 publishKnowledge:(id)=>DEMO_MODE?wait({id,status:'published'}):request(`/knowledge/${id}/publish`,{method:'POST',auth:true})
};
