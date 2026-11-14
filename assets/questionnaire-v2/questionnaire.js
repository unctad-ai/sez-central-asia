(() => {
  'use strict';
  const schema=window.AZFA_SCHEMA, sections=schema.sections;
  const all=sections.flatMap(s=>s.questions), byId=Object.fromEntries(all.map(q=>[q.id,q]));
  const $=id=>document.getElementById(id), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const preview=new URLSearchParams(location.search).get('preview')==='1';
  const apiRoot='/api/v2/';
  let token=new URLSearchParams(location.hash.slice(1)).get('q'), answers={},dirty={},revision=0,current=sections[0].id;
  let timer, flight=null, conflict=false, participant=null, recordStatus='draft', serverAvailable=false, closed=false, submitting=false, uploadPromise=null, files=[];
  const isAnswered=v=>v!==undefined&&v!==null&&v!==''&&(!Array.isArray(v)||v.length>0);
  function visible(q, seen=new Set()) {
    if(!q.visibleIf)return true;
    if(seen.has(q.id))return false;seen.add(q.id);
    const parent=byId[q.visibleIf.question];if(!parent||!visible(parent,seen))return false;
    const value=answers[parent.id],values=Array.isArray(value)?value:[value];
    return values.some(v=>q.visibleIf.in.includes(v));
  }
  async function api(path,method='GET',body) {
    const r=await fetch(apiRoot+path,{method,headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,cache:'no-store',credentials:'omit'});
    let data;try{data=await r.json();}catch{data={};}
    if(!r.ok){const e=new Error(data.error||'Request failed');e.status=r.status;throw e;}return data;
  }
  function saveState(text){$('save-status').textContent=text;}
  function selectedOptions(q){if(!q.filterFrom)return q.options;return q.options.filter(o=>(answers[q.filterFrom]||[]).includes(o)||(q.alwaysOptions||[]).includes(o));}
  function control(q) {
    const help=q.help?` aria-describedby="help-${q.id}"`:'';
    if(q.type==='text'||q.type==='number')return `<input class="input" id="input-${q.id}" data-q="${q.id}" type="${q.type==='number'?'number':'text'}" aria-labelledby="label-${q.id}"${help} maxlength="${q.maxLength||2000}">`;
    if(q.type==='textarea')return `<textarea id="input-${q.id}" data-q="${q.id}" aria-labelledby="label-${q.id}"${help} maxlength="${q.maxLength||4000}" rows="3"></textarea>${q.attach?`<div class="attachment"><label for="file-${q.id}">Adjuntar una norma pública, opcional</label><p class="help">PDF, DOCX o texto, hasta 5 MB cada uno; máximo tres documentos.${preview?' En este recorrido no se suben archivos.':''}</p><input id="file-${q.id}" type="file" data-upload="${q.id}" accept=".pdf,.docx,.txt" ${preview?'disabled':''}><p id="file-status-${q.id}" class="small" role="status"></p><ul id="file-list-${q.id}"></ul></div>`:''}`;
    if(q.presentation==='select')return `<select id="input-${q.id}" data-q="${q.id}" aria-labelledby="label-${q.id}"${help}><option value="">Seleccione cuando haya identificado una prioridad</option>${selectedOptions(q).map(o=>`<option value="${esc(o)}">${esc(o)}</option>`).join('')}</select>`;
    return `<div class="choices">${q.options.map((o,i)=>`<label class="choice" for="input-${q.id}-${i}"><input id="input-${q.id}-${i}" data-q="${q.id}" name="${q.id}" type="${q.type==='multi'?'checkbox':'radio'}" value="${esc(o)}"${help}><span>${esc(o)}</span></label>`).join('')}</div>`;
  }
  function build() {
    $('question-sections').innerHTML=sections.map(s=>`<section class="form-card" id="section-${s.id}" aria-labelledby="heading-${s.id}"><h2 id="heading-${s.id}" tabindex="-1">${esc(s.title)}</h2><p class="intro">${esc(s.intro)}</p>${s.questions.map(q=>`<fieldset class="question" id="question-${q.id}"><legend id="label-${q.id}">${esc(q.label)}</legend>${q.help?`<p class="help" id="help-${q.id}">${esc(q.help)}</p>`:''}${control(q)}</fieldset>`).join('')}<div class="button-row"><button class="btn secondary" type="button" data-prev="${s.id}">Anterior</button><button class="btn" type="button" data-next="${s.id}">${s.id==='seguimiento'||s.id==='tramite'?'Revisar respuestas':'Continuar'}</button></div></section>`).join('');
    $('question-nav').innerHTML=sections.map((s,i)=>`${i===5?'<div class="optional-label">Ampliaciones opcionales</div>':''}<button type="button" data-section="${s.id}">${esc(s.title)}</button>`).join('')+'<button type="button" data-section="resumen">Revisar respuestas</button>';
    $('section-select').innerHTML=sections.map(s=>`<option value="${s.id}">${s.kind==='optional'?'Opcional: ':''}${esc(s.title)}</option>`).join('')+'<option value="resumen">Revisar respuestas</option>';
    document.querySelectorAll('[data-section]').forEach(b=>b.addEventListener('click',()=>show(b.dataset.section)));
    document.querySelectorAll('[data-prev]').forEach(b=>b.addEventListener('click',()=>{const i=sections.findIndex(s=>s.id===b.dataset.prev);show(i?sections[i-1].id:sections[0].id);}));
    document.querySelectorAll('[data-next]').forEach(b=>b.addEventListener('click',()=>{const i=sections.findIndex(s=>s.id===b.dataset.next);show(['seguimiento','tramite'].includes(b.dataset.next)?'resumen':sections[i+1]?.id||'resumen');}));
    $('section-select').addEventListener('change',e=>show(e.target.value));
    document.querySelectorAll('[data-q]').forEach(el=>el.addEventListener(['radio','checkbox'].includes(el.type)||el.tagName==='SELECT'?'change':'input',()=>change(el)));
    document.querySelectorAll('[data-upload]').forEach(el=>el.addEventListener('change',()=>upload(el)));
    hydrate();applyVisibility();renderFiles();show(current,false);
  }
  function renderFiles(){all.filter(q=>q.attach).forEach(q=>{const attached=files.filter(f=>f.question_id===q.id),input=$('file-'+q.id);if(input)input.disabled=attached.length>=3;const list=$('file-list-'+q.id);if(list)list.innerHTML=attached.map(f=>`<li><a href="${apiRoot}q/${encodeURIComponent(token)}/files/${encodeURIComponent(f.id)}" download>${esc(f.filename)}</a> <span class="small">(${Math.ceil(f.size/1024)} KB)</span></li>`).join('');});}
  function upload(el){
    if(preview||!el.files.length)return;
    const file=el.files[0],qid=el.dataset.upload,status=$('file-status-'+qid);
    if(file.size>5*1024*1024){status.textContent='El archivo supera 5 MB. Elija uno más pequeño o indique un enlace.';el.value='';return;}
    el.disabled=true;status.textContent='Guardando el archivo…';
    uploadPromise=(async()=>{try{const content=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file);});const result=await api('q/'+encodeURIComponent(token)+'/files','POST',{question_id:qid,filename:file.name,content_base64:content});files.push(result.file);recordStatus=result.status||recordStatus;if(recordStatus==='amended'){$('submission-status').hidden=false;$('submission-status').textContent='Se ha añadido documentación después del envío. Puede volver a marcar la respuesta para revisión.';}renderFiles();status.textContent='Archivo guardado.';el.value='';}catch(err){status.textContent=err.status===400?err.message:'No se ha guardado el archivo. Compruebe el formato, el tamaño y la conexión; puede volver a seleccionarlo.';}finally{el.disabled=submitting||files.filter(f=>f.question_id===qid).length>=3;uploadPromise=null;}})();
  }
  function hydrate() {
    document.querySelectorAll('[data-q]').forEach(el=>{
      const v=answers[el.dataset.q];
      if(el.type==='radio')el.checked=v===el.value;
      else if(el.type==='checkbox')el.checked=Array.isArray(v)&&v.includes(el.value);
      else el.value=v??'';
    });
  }
  function applyVisibility() {
    all.forEach(q=>$('question-'+q.id).hidden=!visible(q));
    all.filter(q=>q.filterFrom).forEach(q=>{const el=$('input-'+q.id),options=selectedOptions(q);el.innerHTML='<option value="">Seleccione cuando haya identificado una prioridad</option>'+options.map(o=>`<option value="${esc(o)}">${esc(o)}</option>`).join('');el.value=answers[q.id]||'';});
    const core=all.filter(q=>q.progress&&visible(q));const done=core.filter(q=>isAnswered(answers[q.id])).length;
    $('core-progress').max=core.length;$('core-progress').value=done;$('progress-text').textContent=`${done} / ${core.length}`;
    document.dispatchEvent(new Event('azfa:selects-updated'));
  }
  function change(el) {
    const q=byId[el.dataset.q];let v;
    if(q.type==='multi'){
      const controls=[...document.querySelectorAll(`[data-q="${q.id}"]`)];
      if(el.checked&&(q.exclusive||[]).includes(el.value))controls.filter(x=>x!==el).forEach(x=>x.checked=false);
      else if(el.checked)controls.filter(x=>(q.exclusive||[]).includes(x.value)).forEach(x=>x.checked=false);
      v=controls.filter(x=>x.checked).map(x=>x.value);
    }else if(q.type==='number')v=el.value===''?null:Number(el.value);else v=el.value;
    answers[q.id]=v;dirty[q.id]=v;
    // Clear dependent content when its meaning is no longer applicable.
    let changed=true;while(changed){changed=false;for(const item of all){if(!visible(item)&&isAnswered(answers[item.id])){delete answers[item.id];dirty[item.id]=null;document.querySelectorAll('[data-q="'+item.id+'"]').forEach(c=>{if(['radio','checkbox'].includes(c.type))c.checked=false;else c.value='';});changed=true;}}}
    for(const item of all.filter(x=>x.filterFrom)){if(isAnswered(answers[item.id])&&!selectedOptions(item).includes(answers[item.id])){delete answers[item.id];dirty[item.id]=null;}}
    applyVisibility();
    if(preview){saveState('Modo de revisión · sin almacenamiento');return;}
    if(recordStatus==='submitted'||recordStatus==='amended'){$('submission-status').hidden=false;$('submission-status').textContent='Hay cambios posteriores al envío. Puede volver a marcar la respuesta para revisión cuando termine.';}
    saveState('Cambios pendientes de guardar');clearTimeout(timer);timer=setTimeout(()=>flush().catch(()=>{}),650);
  }
  async function flush() {
    clearTimeout(timer);if(preview)return;if(conflict)throw new Error('conflict');if(flight)return flight;
    flight=(async()=>{
      while(Object.keys(dirty).length){
        const batch={...dirty};dirty={};saveState('Guardando…');
        try {const r=await api('q/'+encodeURIComponent(token),'PATCH',{changes:batch,revision});revision=r.revision;recordStatus=r.status;$('save-error').hidden=true;}
        catch(e){dirty={...batch,...dirty};conflict=e.status===409;$('save-error').hidden=false;$('save-error-text').textContent=conflict?'Esta respuesta ha cambiado en otra pestaña o sesión. Sus cambios pendientes se conservan aquí. Descárguelos antes de recargar el enlace para compararlos con la versión guardada.':'No se ha podido guardar. Sus cambios siguen en esta página. Reintente cuando se recupere la conexión o descargue una copia.';$('retry-save').hidden=conflict;saveState('Hay cambios sin guardar');throw e;}
      }
      saveState('Guardado');
    })().finally(()=>{flight=null;});return flight;
  }
  function show(id,focus=true) {
    current=id;sections.forEach(s=>$('section-'+s.id).hidden=s.id!==id);$('summary-panel').hidden=id!=='resumen';
    document.querySelectorAll('#question-nav [data-section]').forEach(b=>{b.classList.toggle('current',b.dataset.section===id);if(b.dataset.section===id)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');});
    $('section-select').value=id;if(id==='resumen')renderSummary();
    document.dispatchEvent(new Event('azfa:selects-updated'));
    if(focus){const target=id==='resumen'?$('summary-panel'):$('heading-'+id);target.setAttribute('tabindex','-1');target.focus({preventScroll:true});target.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});}
  }
  function renderSummary() {
    $('answer-summary').innerHTML=sections.map(s=>{const qs=s.questions.filter(q=>visible(q)&&(s.kind==='core'||isAnswered(answers[q.id])));if(!qs.length)return '';return `<section><h3>${esc(s.title)}</h3><dl>${qs.map(q=>`<dt>${esc(q.label)}</dt><dd${q.options||!isAnswered(answers[q.id])?' data-choice':''}>${esc(isAnswered(answers[q.id])?(Array.isArray(answers[q.id])?answers[q.id].join('; '):answers[q.id]):'Sin respuesta todavía')}</dd>`).join('')}</dl></section>`;}).join('');
  }
  function download() {
    const active=Object.fromEntries(all.filter(q=>visible(q)&&isAnswered(answers[q.id])).map(q=>[q.id,answers[q.id]]));
    const blob=new Blob([JSON.stringify({version:schema.version,mode:preview?'preview':'record',participant,answers:active,pending_changes:dirty},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='central-asia-sez-answers.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  async function startRecord(data,emailStatus) {
    answers=data.answers||{};revision=data.revision||0;recordStatus=data.status||'draft';participant=data.participant;files=data.files||[];
    $('registration-view').hidden=true;$('questionnaire-view').hidden=false;
    $('participant-identity').textContent=`${participant.institution} · ${participant.country} · ${participant.name}`;
    $('resume-box').hidden=false;$('resume-link').value=location.origin+location.pathname+'#q='+encodeURIComponent(token);
    $('mail-status').textContent=emailStatus==='accepted'?'El servicio de correo ha aceptado el mensaje con su enlace.':emailStatus==='failed'?'No se pudo enviar el correo. Guarde el enlace personal que aparece aquí y contacte a nelson.perez@un.org si necesita ayuda.':'Puede volver a este cuestionario mediante su enlace personal.';
    $('submit-note').textContent='Al marcar la respuesta para revisión se registra el envío. El enlace seguirá permitiendo correcciones posteriores.';
    if(recordStatus!=='draft'){$('submission-status').hidden=false;$('submission-status').textContent=recordStatus==='submitted'?'Respuesta marcada para revisión. Puede seguir corrigiéndola.':'Esta respuesta contiene cambios posteriores al último envío.';}
    saveState('Guardado');build();
  }
  $('registration-form').addEventListener('submit',async e=>{
    e.preventDefault();if(!serverAvailable)return;
    const button=e.target.querySelector('button[type=submit]');button.disabled=true;$('registration-error').hidden=true;
    const body=Object.fromEntries(new FormData(e.target));body.notice_accepted=e.target.elements.notice_accepted.checked;
    if(!e.target.dataset.requestId)e.target.dataset.requestId=crypto.randomUUID();body.request_id=e.target.dataset.requestId;
    try{const result=await api('register','POST',body);token=result.token;history.replaceState(null,'',location.pathname+'#q='+encodeURIComponent(token));const data=await api('q/'+encodeURIComponent(token));await startRecord(data,result.email_status);$('questionnaire-view').scrollIntoView({block:'start'});}
    catch(err){$('registration-error').hidden=false;$('registration-error').textContent=err.status===409?'El registro cambió durante un reintento. Recargue la página para iniciar un registro nuevo.':'No se ha podido crear el registro. Compruebe los datos y que el servicio esté disponible.';}
    finally{button.disabled=false;}
  });
  $('copy-link').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('resume-link').value);$('copy-status').textContent='Enlace copiado';}catch{$('resume-link').select();$('copy-status').textContent='Seleccione y copie el enlace.';}});
  $('retry-save').addEventListener('click',()=>flush().catch(()=>{}));
  $('download-local').addEventListener('click',download);$('download-answers').addEventListener('click',download);
  $('submit-answers').addEventListener('click',async()=>{
    if(preview){$('submission-status').hidden=false;$('submission-status').textContent='Recorrido de revisión completado. No se han guardado ni enviado respuestas.';$('submission-status').scrollIntoView({block:'center'});return;}
    const b=$('submit-answers');submitting=true;const locked=[...document.querySelectorAll('#questionnaire-view input,#questionnaire-view select,#questionnaire-view textarea,#questionnaire-view button')].map(el=>[el,el.disabled]);locked.forEach(([el])=>el.disabled=true);
    try{if(uploadPromise)await uploadPromise;await flush();const result=await api('q/'+encodeURIComponent(token)+'/submit','POST',{revision});revision=result.revision;recordStatus='submitted';$('submission-status').hidden=false;$('submission-status').textContent='Respuesta enviada para revisión. Puede seguir corrigiéndola con su enlace.';$('submission-status').scrollIntoView({block:'center'});saveState('Guardado y marcado para revisión');}
    catch{$('save-error').hidden=false;if(!$('save-error-text').textContent)$('save-error-text').textContent='No se ha podido registrar el envío. Sus respuestas guardadas se conservan. Puede reintentarlo.';}
    finally{locked.forEach(([el,wasDisabled])=>el.disabled=el.dataset.upload?false:wasDisabled);submitting=false;b.disabled=false;}
  });
  window.addEventListener('hashchange',()=>{const next=new URLSearchParams(location.hash.slice(1)).get('q');if(next&&next!==token)location.reload();});
  window.addEventListener('beforeunload',e=>{if(!preview&&(Object.keys(dirty).length||flight||submitting||uploadPromise)){e.preventDefault();e.returnValue='';}});
  (async()=>{
    try{const meta=await api('meta');serverAvailable=true;closed=!!meta.closed;}catch{}
    if(preview){$('mode-note').textContent='Puede recorrer las preguntas sin guardar ni enviar respuestas.';$('questionnaire-view').hidden=false;$('participant-identity').textContent='Questionnaire preview · core sections and optional details';$('submit-answers').textContent='Terminar el recorrido de revisión';$('submit-note').textContent='Este recorrido no crea un registro ni envía respuestas.';saveState('Modo de revisión · sin almacenamiento');build();return;}
    $('mode-note').textContent='Sus respuestas se guardan mientras avanza. Puede volver mediante su enlace personal.';
    if(token){try{await startRecord(await api('q/'+encodeURIComponent(token)));if(closed){$('mode-note').textContent='La consulta está cerrada. Puede consultar sus respuestas, pero ya no modificarlas.';document.querySelectorAll('#questionnaire-view [data-q],#questionnaire-view [data-upload],#submit-answers,#retry-save').forEach(el=>el.disabled=true);}}catch{$('load-error').hidden=false;$('load-error').innerHTML='No se ha podido abrir este enlace. Compruebe que está completo y que el servicio está disponible. <a href="/questionnaire/">Back to registration</a>.';}return;}
    $('registration-view').hidden=false;
    if(closed){$('registration-view').querySelector('h2').textContent='Consulta cerrada';$('registration-view').querySelector('p').textContent='La consulta ya no acepta nuevas respuestas. Si necesita información, escriba a nelson.perez@un.org.';$('registration-form').hidden=true;$('mode-note').textContent='La consulta está cerrada.';return;}
    if(!serverAvailable){$('registration-error').classList.add('service-notice');$('registration-form').querySelector('button[type=submit]').disabled=true;$('registration-error').hidden=false;$('registration-error').innerHTML='<a href="/questionnaire/?preview=1">You can review the questions without registering</a>.';}
  })();
})();
