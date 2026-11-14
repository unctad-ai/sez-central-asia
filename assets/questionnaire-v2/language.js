(() => {
  'use strict';
  const dictionary=window.AZFA_EN;
  const originals=new WeakMap(), attributes=new WeakMap();
  let lang=new URLSearchParams(location.search).get('lang');
  
  lang='en';
  const excluded='script,style,textarea,#participant-identity,#file-list,dd:not([data-choice]),[data-no-translate],.attachment li';
  function translated(text){return lang==='en'?(dictionary[text]||text):text;}
  function render(){
    observer.disconnect();
    // Explicit values keep registration and conditional-answer semantics stable.
    document.querySelectorAll('option:not([value])').forEach(o=>o.setAttribute('value',o.textContent));
    const walker=document.createTreeWalker(document.documentElement,NodeFilter.SHOW_TEXT);
    let node;
    while((node=walker.nextNode())){
      if(!node.parentElement||node.parentElement.closest(excluded))continue;
      const raw=node.nodeValue,key=raw.trim();if(!key)continue;
      let saved=originals.get(node);
      if(!saved||raw!==saved.rendered){saved={original:raw,rendered:raw};originals.set(node,saved);}
      const original=saved.original,trimmed=original.trim();
      let output=translated(trimmed);
      if(node.parentElement.matches('dd[data-choice]'))output=trimmed.split('; ').map(translated).join('; ');
      saved.rendered=original.replace(trimmed,output);if(node.nodeValue!==saved.rendered)node.nodeValue=saved.rendered;
    }
    document.querySelectorAll('[placeholder],[aria-label],[title]').forEach(el=>{
      let saved=attributes.get(el);if(!saved){saved={};attributes.set(el,saved);}
      for(const name of ['placeholder','aria-label','title']){
        if(!el.hasAttribute(name))continue;
        saved[name]??=el.getAttribute(name);const next=translated(saved[name]);if(el.getAttribute(name)!==next)el.setAttribute(name,next);
      }
    });
    document.documentElement.lang=lang;
    document.querySelectorAll('[data-language]').forEach(b=>{b.classList.toggle('is-on',b.dataset.language===lang);b.setAttribute('aria-pressed',String(b.dataset.language===lang));});
    observer.observe(document.body,{subtree:true,childList:true,characterData:true});
    document.dispatchEvent(new Event('azfa:language-changed'));
  }
  const observer=new MutationObserver(render);
  document.querySelectorAll('[data-language]').forEach(button=>button.addEventListener('click',()=>{
    lang=button.dataset.language;try{localStorage.setItem('azfa-questionnaire-language',lang);}catch{}
    const url=new URL(location.href);url.searchParams.set('lang',lang);history.replaceState(null,'',url);
    render();
  }));
  render();
})();
