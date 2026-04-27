(function(){
  'use strict';
  const KIND = {
    agent: {c:'#8b5cf6', s:'#ddd6fe', r:26, shape:'hex', label:'Agent'},
    skill: {c:'#06b6d4', s:'#cffafe', r:22, shape:'round', label:'Skill'},
    tool: {c:'#f59e0b', s:'#fde68a', r:24, shape:'diamond', label:'Tool'},
    workflow: {c:'#fb7185', s:'#ffe4e6', r:23, shape:'round', label:'Workflow'},
    part: {c:'#10b981', s:'#bbf7d0', r:25, shape:'circle', label:'Part'},
    rule: {c:'#64748b', s:'#e2e8f0', r:21, shape:'tag', label:'Rule'},
    document: {c:'#38bdf8', s:'#dbeafe', r:20, shape:'doc', label:'Document'},
    note: {c:'#3b82f6', s:'#bfdbfe', r:20, shape:'circle', label:'Note'},
  };
  function clamp(v,a,b){ return Math.max(a, Math.min(b, v)); }
  function kindOf(k){ k=String(k||'note').toLowerCase(); if(k.includes('agent'))return'agent'; if(k.includes('skill'))return'skill'; if(k.includes('tool'))return'tool'; if(k.includes('workflow'))return'workflow'; if(k.includes('part'))return'part'; if(k.includes('rule')||k.includes('policy'))return'rule'; if(k.includes('document')||k.includes('case')||k.includes('sop'))return'document'; return'note'; }
  function short(t,n){ t=String(t||''); return t.length>n?t.slice(0,n-1)+'…':t; }
  function curvePoint(a,b,t,offset){ const x=a.x+(b.x-a.x)*t, y=a.y+(b.y-a.y)*t; const dx=b.x-a.x, dy=b.y-a.y; const len=Math.hypot(dx,dy)||1; return {x:x+(-dy/len)*offset, y:y+(dx/len)*offset}; }
  class NoteGraphForce {
    constructor(dom, graph, options){
      this.dom=dom; this.options=options||{}; this.small=!!this.options.small; this.selected=null; this.hover=null; this.scale=1; this.tx=0; this.ty=0; this.dragNode=null; this.dragCanvas=false; this.last={x:0,y:0}; this.running=true;
      this.canvas=document.createElement('canvas'); this.canvas.className='离线图谱Canvas'; this.ctx=this.canvas.getContext('2d'); dom.innerHTML=''; dom.appendChild(this.canvas);
      this.resize(); this.setData(graph||{}); this.bind(); this.fitView(false); this.start();
    }
    resize(){ const dpr=window.devicePixelRatio||1; const r=this.dom.getBoundingClientRect(); this.w=Math.max(360, r.width||900); this.h=Math.max(this.small?220:560, r.height||(this.small?240:650)); this.canvas.style.width=this.w+'px'; this.canvas.style.height=this.h+'px'; this.canvas.width=this.w*dpr; this.canvas.height=this.h*dpr; this.ctx.setTransform(dpr,0,0,dpr,0,0); }
    setData(graph){
      const rawNodes=[...(graph.nodes||[])].slice(0,this.options.limit||240); const ids=new Set(rawNodes.map(n=>n.id)); const rawEdges=[...((graph.visible_edges&&graph.visible_edges.length?graph.visible_edges:graph.edges)||[])].filter(e=>ids.has(e.source)&&ids.has(e.target)).slice(0,(this.options.limit||240)*2);
      const groups={agent:0,skill:1,tool:2,workflow:3,part:4,rule:5,document:6,note:7}; const R=Math.min(this.w,this.h)*(this.small?.25:.36); const cx=this.w/2, cy=this.h/2;
      this.nodes=rawNodes.map((n,i)=>{ const k=kindOf(n.kind); const a=(groups[k]/8)*Math.PI*2 + (i%17)*0.035; const rr=R*(0.45+((i%11)/16)); return {id:n.id,label:short(n.title||n.id,this.small?8:16),title:n.title||n.id,kind:n.kind||'Note',type:k,status:n.status||'',maturity:n.maturity||'',x:cx+Math.cos(a)*rr+(Math.random()-.5)*40,y:cy+Math.sin(a)*rr+(Math.random()-.5)*40,vx:0,vy:0,r:(KIND[k]||KIND.note).r*(this.small?.72:1)}; });
      this.nodeMap=new Map(this.nodes.map(n=>[n.id,n])); this.edges=rawEdges.map((e,i)=>({id:e.edge_id||'e'+i,source:e.source,target:e.target,predicate:e.predicate||'',kind:e.kind||'',status:e.status||'',a:this.nodeMap.get(e.source),b:this.nodeMap.get(e.target)})).filter(e=>e.a&&e.b);
      this.neighbor=new Map(); this.nodes.forEach(n=>this.neighbor.set(n.id,new Set([n.id]))); this.edges.forEach(e=>{this.neighbor.get(e.source)?.add(e.target); this.neighbor.get(e.target)?.add(e.source);}); this.iter=0;
    }
    bind(){
      window.addEventListener('resize',()=>{ if(!this.running)return; this.resize(); this.draw(); });
      this.canvas.addEventListener('wheel',e=>{ e.preventDefault(); const old=this.scale; const delta=e.deltaY>0?.9:1.1; const ns=clamp(old*delta,.2,3); const p=this.screenToWorld(e.offsetX,e.offsetY); this.scale=ns; this.tx=e.offsetX-p.x*ns; this.ty=e.offsetY-p.y*ns; this.draw(); },{passive:false});
      this.canvas.addEventListener('mousedown',e=>{ const n=this.hit(e.offsetX,e.offsetY); this.last={x:e.offsetX,y:e.offsetY}; if(n){this.dragNode=n; n.fixed=true;} else {this.dragCanvas=true;} });
      this.canvas.addEventListener('mousemove',e=>{ const p=this.screenToWorld(e.offsetX,e.offsetY); if(this.dragNode){this.dragNode.x=p.x; this.dragNode.y=p.y; this.dragNode.vx=0; this.dragNode.vy=0; this.draw(); return;} if(this.dragCanvas){this.tx+=e.offsetX-this.last.x; this.ty+=e.offsetY-this.last.y; this.last={x:e.offsetX,y:e.offsetY}; this.draw(); return;} const h=this.hit(e.offsetX,e.offsetY); if(h!==this.hover){this.hover=h; this.canvas.style.cursor=h?'pointer':'grab'; this.draw();} });
      this.canvas.addEventListener('mouseup',()=>{ if(this.dragNode)this.dragNode.fixed=false; this.dragNode=null; this.dragCanvas=false; });
      this.canvas.addEventListener('mouseleave',()=>{this.dragNode=null; this.dragCanvas=false; this.hover=null; this.draw();});
      this.canvas.addEventListener('click',e=>{ const n=this.hit(e.offsetX,e.offsetY); if(n){ this.selectNode(n.id); this.options.onSelect&&this.options.onSelect(n.id); } else { this.clear(); this.options.onClear&&this.options.onClear(); } });
    }
    screenToWorld(x,y){return {x:(x-this.tx)/this.scale,y:(y-this.ty)/this.scale};}
    worldToScreen(x,y){return {x:x*this.scale+this.tx,y:y*this.scale+this.ty};}
    hit(x,y){ const p=this.screenToWorld(x,y); for(let i=this.nodes.length-1;i>=0;i--){ const n=this.nodes[i]; if(Math.hypot(p.x-n.x,p.y-n.y)<n.r+8) return n; } return null; }
    start(){ const loop=()=>{ if(!this.running)return; if(this.iter<420){ this.step(); this.iter++; } this.draw(); requestAnimationFrame(loop); }; requestAnimationFrame(loop); }
    relayout(){ this.iter=0; this.nodes.forEach((n,i)=>{ n.vx+=(Math.random()-.5)*8; n.vy+=(Math.random()-.5)*8; n.fixed=false; }); }
    step(){ const cx=this.w/2, cy=this.h/2; const alpha=Math.max(.02, .75*(1-this.iter/430));
      for(let i=0;i<this.nodes.length;i++){ const a=this.nodes[i]; for(let j=i+1;j<this.nodes.length;j++){ const b=this.nodes[j]; let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+.01; const f=(this.small?900:2200)/d2*alpha; const d=Math.sqrt(d2); dx/=d; dy/=d; a.vx+=dx*f; a.vy+=dy*f; b.vx-=dx*f; b.vy-=dy*f; }}
      this.edges.forEach(e=>{ const a=e.a,b=e.b; const dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1; const target=this.small?72:135; const f=(d-target)*0.012*alpha; const nx=dx/d,ny=dy/d; a.vx+=nx*f; a.vy+=ny*f; b.vx-=nx*f; b.vy-=ny*f; });
      this.nodes.forEach((n)=>{ if(!n.fixed){ n.vx+=(cx-n.x)*0.002*alpha; n.vy+=(cy-n.y)*0.002*alpha; n.vx*=0.86; n.vy*=0.86; n.x+=n.vx; n.y+=n.vy; }});
    }
    fitView(animated=true){ if(!this.nodes.length){this.scale=1;this.tx=0;this.ty=0;return;} let minx=Infinity,miny=Infinity,maxx=-Infinity,maxy=-Infinity; this.nodes.forEach(n=>{minx=Math.min(minx,n.x-n.r);maxx=Math.max(maxx,n.x+n.r);miny=Math.min(miny,n.y-n.r);maxy=Math.max(maxy,n.y+n.r);}); const pad=this.small?30:90; const sx=(this.w-pad*2)/Math.max(1,maxx-minx); const sy=(this.h-pad*2)/Math.max(1,maxy-miny); this.scale=clamp(Math.min(sx,sy),.25,1.8); this.tx=(this.w-(minx+maxx)*this.scale)/2; this.ty=(this.h-(miny+maxy)*this.scale)/2; this.draw(); }
    selectNode(id){ this.selected=id; this.draw(); }
    clear(){ this.selected=null; this.draw(); }
    opacityFor(id){ if(!this.selected) return 1; const set=this.neighbor.get(this.selected); return set&&set.has(id)?1:.08; }
    edgeOpacity(e){ if(!this.selected) return String(e.kind).toLowerCase()==='linked'?.16:.56; return (e.source===this.selected||e.target===this.selected)?.92:.035; }
    drawShape(n, alpha){ const ctx=this.ctx, st=KIND[n.type]||KIND.note; ctx.save(); ctx.globalAlpha=alpha; ctx.shadowColor=st.c; ctx.shadowBlur=this.hover===n||this.selected===n.id?30:12; ctx.fillStyle=st.c; ctx.strokeStyle=st.s; ctx.lineWidth=this.selected===n.id?4:2; ctx.beginPath(); const r=n.r; if(st.shape==='diamond'){ctx.moveTo(n.x,n.y-r);ctx.lineTo(n.x+r,n.y);ctx.lineTo(n.x,n.y+r);ctx.lineTo(n.x-r,n.y);ctx.closePath();} else if(st.shape==='hex'){for(let i=0;i<6;i++){const a=Math.PI/6+i*Math.PI/3; const x=n.x+Math.cos(a)*r, y=n.y+Math.sin(a)*r; i?ctx.lineTo(x,y):ctx.moveTo(x,y);}ctx.closePath();} else if(st.shape==='round'){ctx.roundRect(n.x-r*1.18,n.y-r*.72,r*2.36,r*1.44,10);} else if(st.shape==='tag'){ctx.roundRect(n.x-r,n.y-r*.66,r*2,r*1.32,6); ctx.moveTo(n.x+r*.65,n.y-r*.66);ctx.lineTo(n.x+r,n.y);ctx.lineTo(n.x+r*.65,n.y+r*.66);} else if(st.shape==='doc'){ctx.roundRect(n.x-r*.8,n.y-r,r*1.6,r*2,5); ctx.moveTo(n.x+r*.25,n.y-r);ctx.lineTo(n.x+r*.8,n.y-r*.45);ctx.lineTo(n.x+r*.25,n.y-r*.45);} else {ctx.arc(n.x,n.y,r,0,Math.PI*2);} ctx.fill(); ctx.stroke(); ctx.shadowBlur=0; ctx.fillStyle='#fff'; ctx.font=`700 ${Math.max(10,n.r*.58)}px Inter, sans-serif`; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText((n.kind||'N').slice(0,1).toUpperCase(),n.x,n.y+1); ctx.restore(); }
    draw(){ const ctx=this.ctx; ctx.clearRect(0,0,this.w,this.h); const g=ctx.createLinearGradient(0,0,this.w,this.h); g.addColorStop(0,'#07111f'); g.addColorStop(.55,'#0b1220'); g.addColorStop(1,'#111827'); ctx.fillStyle=g; ctx.fillRect(0,0,this.w,this.h); ctx.save(); ctx.translate(this.tx,this.ty); ctx.scale(this.scale,this.scale);
      this.edges.forEach(e=>{ const a=e.a,b=e.b; const alpha=this.edgeOpacity(e); const kind=String(e.kind||'').toLowerCase(); const col=kind==='runtime'?'#22d3ee':kind==='inferred'?'#c084fc':kind==='linked'?'#64748b':'#94a3b8'; ctx.save(); ctx.globalAlpha=alpha; ctx.strokeStyle=col; ctx.lineWidth=(kind==='runtime'?2.5:kind==='linked'?.65:1.15)/this.scale; if(kind==='linked')ctx.setLineDash([5/this.scale,5/this.scale]); if(kind==='inferred')ctx.setLineDash([2/this.scale,5/this.scale]); const dx=b.x-a.x,dy=b.y-a.y; const off=clamp(Math.hypot(dx,dy)*.08,10,46); const m=curvePoint(a,b,.5,off); ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.quadraticCurveTo(m.x,m.y,b.x,b.y); ctx.stroke(); ctx.restore(); });
      this.nodes.forEach(n=>this.drawShape(n,this.opacityFor(n.id)));
      this.nodes.forEach(n=>{ const alpha=this.opacityFor(n.id); if(alpha<.12)return; ctx.save(); ctx.globalAlpha=alpha; ctx.font=`700 ${this.small?10:12}px Inter, sans-serif`; ctx.textAlign='center'; ctx.textBaseline='top'; ctx.fillStyle='#e5e7eb'; ctx.strokeStyle='#020617'; ctx.lineWidth=4/this.scale; ctx.strokeText(n.label,n.x,n.y+n.r+8); ctx.fillText(n.label,n.x,n.y+n.r+8); ctx.restore(); });
      ctx.restore();
      if(this.hover){ const p=this.worldToScreen(this.hover.x,this.hover.y); ctx.save(); ctx.fillStyle='rgba(15,23,42,.88)'; ctx.strokeStyle='rgba(148,163,184,.45)'; ctx.lineWidth=1; const w=260,h=72,x=clamp(p.x+18,10,this.w-w-10),y=clamp(p.y+18,10,this.h-h-10); ctx.roundRect(x,y,w,h,14); ctx.fill(); ctx.stroke(); ctx.fillStyle='#f8fafc'; ctx.font='700 13px Inter, sans-serif'; ctx.fillText(short(this.hover.title,28),x+16,y+18); ctx.fillStyle='#93c5fd'; ctx.font='11px ui-monospace, monospace'; ctx.fillText(this.hover.id,x+16,y+40); ctx.fillStyle='#cbd5e1'; ctx.font='11px Inter, sans-serif'; ctx.fillText(`${this.hover.kind} · ${this.hover.status||'未标注'}`,x+16,y+59); ctx.restore(); }
    }
    destroy(){ this.running=false; this.dom.innerHTML=''; }
  }
  window.NoteGraphForce = {
    version:'0.1.0-local-offline',
    mount(dom, graph, options){ return new NoteGraphForce(dom, graph, options||{}); }
  };
})();
