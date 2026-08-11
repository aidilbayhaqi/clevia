import {API_URL,TOKEN_KEY} from '../config';
export async function request(path,{method='GET',body,auth=false,headers={}}={}){
 const h={'Content-Type':'application/json',...headers};
 if(auth){const t=localStorage.getItem(TOKEN_KEY); if(t) h.Authorization=`Bearer ${t}`;}
 const res=await fetch(`${API_URL}${path}`,{method,headers:h,body:body===undefined?undefined:JSON.stringify(body)});
 const data=await res.json().catch(()=>null);
 if(!res.ok){throw new Error(data?.detail||data?.message||`Request failed (${res.status})`)}
 return data;
}
