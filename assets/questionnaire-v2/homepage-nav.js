(() => {
 const header=document.querySelector('.site-header');
 function update(){ const scrolled=window.scrollY>24; header.classList.toggle('is-scrolled',scrolled); const width=window.innerWidth; document.documentElement.style.setProperty('--header-height', (width<=540?(scrolled?132:156):width<=1200?(scrolled?88:120):(scrolled?60:88))+'px'); }
 window.addEventListener('scroll',update,{passive:true});window.addEventListener('resize',update);window.addEventListener('pageshow',update);update();
})();
