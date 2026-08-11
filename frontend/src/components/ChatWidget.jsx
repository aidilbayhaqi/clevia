import {Bot,MessageCircle,Send,X,Sparkles} from '../icons';
import {useState} from 'react';
import {publicApi} from '../api/publicApi';

const QUICK_PROMPTS=[
  'Treatment yang cocok untuk kulit kusam',
  'Cek jadwal dokter',
  'Saya mau booking konsultasi',
];

export default function ChatWidget(){
  const [open,setOpen]=useState(false);
  const [text,setText]=useState('');
  const [conversation,setConversation]=useState(null);
  const [loading,setLoading]=useState(false);
  const [messages,setMessages]=useState([
    {role:'assistant',content:'Halo, saya Clevia AI Concierge. Saya bisa bantu menjelaskan treatment, mencari jadwal, dan membantu proses booking.'}
  ]);

  async function sendMessage(raw){
    const msg=String(raw||'').trim();
    if(!msg||loading)return;
    setText('');
    setMessages(x=>[...x,{role:'user',content:msg}]);
    setLoading(true);
    try{
      let c=conversation;
      if(!c){
        c=await publicApi.createConversation();
        setConversation(c);
      }
      const r=await publicApi.sendMessage(c,{message:msg});
      const answer=r.message||r.response||r.content||'Pesan Anda sudah diterima. Tim Clevia akan membantu langkah selanjutnya.';
      setMessages(x=>[...x,{role:'assistant',content:answer}]);
    }catch(err){
      setMessages(x=>[...x,{role:'assistant',content:`Maaf, koneksi sedang bermasalah. ${err.message}`}]);
    }finally{
      setLoading(false);
    }
  }

  function submit(e){
    e.preventDefault();
    sendMessage(text);
  }

  return <>
    <button className="chat-fab" onClick={()=>setOpen(true)} aria-label="Buka Clevia AI Concierge">
      <span><MessageCircle/></span>
      <em><small>CLEVIA</small>AI Concierge</em>
    </button>

    {open&&<div className="chat-panel" role="dialog" aria-label="Clevia AI Concierge">
      <header className="chat-panel__header">
        <div className="chat-avatar"><Sparkles/></div>
        <div className="chat-title">
          <span>AI CONCIERGE</span>
          <b>Clevia Assistant</b>
          <small><i/> Available now</small>
        </div>
        <button className="chat-close" onClick={()=>setOpen(false)} aria-label="Tutup chat"><X/></button>
      </header>

      <div className="chat-intro">
        <span className="chat-intro__mark">C</span>
        <div>
          <small>WELCOME TO CLEVIA</small>
          <strong>How may we assist you today?</strong>
          <p>Tanyakan treatment, dokter, jadwal, atau mulai booking langsung dari sini.</p>
        </div>
      </div>

      {messages.length<=1&&<div className="chat-quick">
        {QUICK_PROMPTS.map(item=><button key={item} onClick={()=>sendMessage(item)}>{item}</button>)}
      </div>}

      <div className="chat-body">
        {messages.map((m,i)=><div key={i} className={`chat-message chat-message--${m.role}`}>
          {m.role==='assistant'&&<span className="chat-message__avatar"><Bot/></span>}
          <div className="chat-message__bubble">{m.content}</div>
        </div>)}
        {loading&&<div className="chat-typing" aria-label="Clevia sedang mengetik"><i/><i/><i/></div>}
      </div>

      <form onSubmit={submit} className="chat-input">
        <div className="chat-composer">
          <input value={text} onChange={e=>setText(e.target.value)} placeholder="Tulis pesan untuk Clevia..." aria-label="Pesan"/>
          <button disabled={!text.trim()||loading} aria-label="Kirim pesan"><Send/></button>
        </div>
        <small>AI membantu informasi dan layanan administratif. Keputusan medis tetap oleh tenaga kesehatan.</small>
      </form>
    </div>}
  </>;
}
