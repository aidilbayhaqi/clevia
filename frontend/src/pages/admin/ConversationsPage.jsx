import {useEffect,useState} from 'react';
import {Bot,Headphones,MessageSquareText,Send,UserRound} from '../../icons';
import {crmApi} from '../../api/crmApi';
import {Badge,PageHead} from '../../components/Ui';
import {dateTimeID} from '../../utils/format';

export default function ConversationsPage(){
  const [items,setItems]=useState([]);
  const [selected,setSelected]=useState(null);
  const [msgs,setMsgs]=useState([]);
  const [error,setError]=useState('');
  const [reply,setReply]=useState('');
  const [sending,setSending]=useState(false);

  useEffect(()=>{
    crmApi.conversations()
      .then(rows=>{
        setItems(rows);
        if(rows[0]) select(rows[0]);
      })
      .catch(e=>setError(e.message));
  },[]);

  async function select(conversation){
    setSelected(conversation);
    setError('');
    try{
      setMsgs(await crmApi.transcript(conversation.id));
    }catch(e){
      setMsgs([]);
      setError(e.message);
    }
  }

  function updateSelected(patch){
    setSelected(current=>current?{...current,...patch}:current);
    setItems(current=>current.map(item=>item.id===selected?.id?{...item,...patch}:item));
  }

  async function toggle(){
    if(!selected)return;
    setError('');
    try{
      const isHuman=selected.status==='human_active';
      const result=await (isHuman?crmApi.release(selected.id):crmApi.takeover(selected.id));
      updateSelected({status:result.status,agent_state:result.agent_state||selected.agent_state});
    }catch(e){
      setError(e.message);
    }
  }

  async function resolve(){
    if(!selected)return;
    setError('');
    try{
      const result=await crmApi.resolve(selected.id);
      updateSelected({status:result.status,agent_state:result.agent_state||'CLOSED'});
    }catch(e){
      setError(e.message);
    }
  }

  async function sendReply(event){
    event.preventDefault();
    const message=reply.trim();
    if(!selected||!message||selected.status!=='human_active')return;
    setSending(true);
    setError('');
    try{
      const created=await crmApi.reply(selected.id,message);
      setMsgs(current=>[...current,created]);
      setReply('');
    }catch(e){
      setError(e.message);
    }finally{
      setSending(false);
    }
  }

  async function feedback(message,rating){
    if(!selected||!message.id)return;
    setError('');
    try{
      await crmApi.feedback(selected.id,message.id,rating);
      setMsgs(current=>current.map(item=>item.id===message.id?{...item,_feedback:rating}:item));
    }catch(e){
      setError(e.message);
    }
  }

  return <>
    <PageHead
      title="AI Conversations"
      subtitle="Monitor grounded AI conversations, handoff context, and human takeover."
    />
    <div className="conversation-shell">
      <aside className="conversation-list">
        <div className="conversation-list__head"><span><MessageSquareText/> Inbox</span><b>{items.length}</b></div>
        {items.map(c=><button className={selected?.id===c.id?'active':''} key={c.id} onClick={()=>select(c)}>
          <span className="conversation-avatar">{(c.visitor_name||'V')[0]}</span>
          <div>
            <b>{c.visitor_name}</b>
            <small>{c.last_message}</small>
            <em>{dateTimeID(c.updated_at)} · {c.channel}</em>
          </div>
          <Badge>{c.status}</Badge>
        </button>)}
      </aside>

      <section className="conversation-view">
        {selected&&<>
          <header>
            <div>
              <span className="conversation-avatar">{(selected.visitor_name||'V')[0]}</span>
              <div>
                <b>{selected.visitor_name}</b>
                <small>{selected.channel==='whatsapp'?'WhatsApp':'Website chat'} · {selected.agent_state||'INFO'}</small>
              </div>
            </div>
            <div style={{display:'flex',gap:8}}>
              {selected.status!=='resolved'&&<button className="btn btn--admin" onClick={toggle}>
                {selected.status==='human_active'?<><Bot/> Release to AI</>:<><Headphones/> Take over</>}
              </button>}
              {selected.status!=='resolved'&&<button className="btn" onClick={resolve}>Resolve</button>}
            </div>
          </header>

          <div className="transcript">
            {error&&<div className="api-gap"><b>Request failed</b><p>{error}</p></div>}
            {selected.handoff_summary&&<div className="api-gap">
              <b>Handoff context</b>
              <p>{selected.handoff_reason||'Human handoff'}</p>
              <small>{selected.handoff_summary}</small>
            </div>}
            {msgs.map((m,i)=><div key={m.id||i} className={`bubble bubble--${m.role}`}>
              <span>{m.role==='assistant'?<Bot/>:<UserRound/>}</span>
              <div>
                <p>{m.content}</p>
                {m.sender_type==='ai'&&<small style={{display:'flex',gap:8,marginTop:6}}>
                  <button type="button" onClick={()=>feedback(m,'good')}>Good</button>
                  <button type="button" onClick={()=>feedback(m,'wrong')}>Wrong</button>
                  <button type="button" onClick={()=>feedback(m,'missing_knowledge')}>Missing knowledge</button>
                  {m._feedback&&<em>Saved: {m._feedback}</em>}
                </small>}
              </div>
            </div>)}
          </div>

          <form onSubmit={sendReply}>
            <footer>
              <input
                value={reply}
                onChange={event=>setReply(event.target.value)}
                disabled={selected.status!=='human_active'||sending}
                placeholder={selected.status==='human_active'?'Reply as clinic staff...':'Take over to reply as clinic staff'}
              />
              <button disabled={selected.status!=='human_active'||sending||!reply.trim()}><Send/></button>
            </footer>
          </form>
        </>}
      </section>

      <aside className="conversation-meta">
        <span className="eyebrow">Conversation</span>
        <h3>Context</h3>
        <dl>
          <dt>Channel</dt><dd>{selected?.channel||'—'}</dd>
          <dt>Control</dt><dd>{selected?.status==='human_active'?'Human':selected?.status==='resolved'?'Closed':'AI / Queue'}</dd>
          <dt>Agent state</dt><dd>{selected?.agent_state||'—'}</dd>
          <dt>Handoff</dt><dd>{selected?.handoff_reason||'—'}</dd>
        </dl>
        <div className="meta-note">AI messages can be traced through backend trace IDs and staff feedback is stored for evaluation.</div>
      </aside>
    </div>
  </>;
}
