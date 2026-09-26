(function(){
  var D=JSON.parse(document.getElementById('data').textContent);

  /* the Frostline logo first: the photo wall and the groups' logos (data-src) start once it is in */
  var later=document.querySelectorAll('img[data-src]'),logo=document.querySelector('.hero-logo img');
  function fill(){
    later.forEach(function(im){
      im.addEventListener('load',function(){im.classList.add('in');});
      im.src=im.getAttribute('data-src');im.removeAttribute('data-src');
    });
  }
  if(later.length){if(!logo||logo.complete)fill();else{logo.addEventListener('load',fill);logo.addEventListener('error',fill);}}

  /* photo rows: arrows on wide screens, swipe everywhere */
  document.querySelectorAll('.worn').forEach(function(w){
    var rail=w.querySelector('.rail'),a=w.querySelectorAll('.arr');
    if(!rail||a.length<2)return;
    function upd(){var max=rail.scrollWidth-rail.clientWidth-2;a[0].disabled=rail.scrollLeft<=2;a[1].disabled=rail.scrollLeft>=max;}
    a.forEach(function(b){b.addEventListener('click',function(){rail.scrollBy({left:(+b.getAttribute('data-dir'))*rail.clientWidth*.9,behavior:'smooth'});});});
    rail.addEventListener('scroll',upd,{passive:true});window.addEventListener('resize',upd);
    rail._upd=upd;upd();
  });

  /* garments as slides (style b): swipe, the arrows, the arrow keys, or pick one by name;
     the name of the slide in view lights up */
  document.querySelectorAll('[data-car]').forEach(function(car){
    var track=car.querySelector('.car-track'),slides=[].slice.call(track.querySelectorAll('.slide')),
        tabRow=car.querySelector('.car-tabs'),tabs=[].slice.call(car.querySelectorAll('.car-tab')),
        arr=car.querySelectorAll('.car-arr'),cur=-1,raf=0;
    if(!slides.length)return;
    function padL(){return parseFloat(getComputedStyle(track).scrollPaddingLeft)||0;}
    function go(k,instant){
      k=Math.max(0,Math.min(slides.length-1,k));
      track.scrollTo({left:slides[k].offsetLeft-padL(),behavior:instant?'auto':'smooth'});
    }
    function mark(){
      raf=0;var x=track.scrollLeft+padL(),best=0,bd=Infinity;
      slides.forEach(function(s,k){var d=Math.abs(s.offsetLeft-x);if(d<bd){bd=d;best=k;}});
      if(best===cur)return;cur=best;
      tabs.forEach(function(t,k){t.setAttribute('aria-current',k===cur?'true':'false');});
      slides.forEach(function(s,k){s.classList.toggle('on',k===cur);});
      var t=tabs[cur];
      if(t&&tabRow.scrollWidth>tabRow.clientWidth)tabRow.scrollTo({left:t.offsetLeft-(tabRow.clientWidth-t.offsetWidth)/2,behavior:'smooth'});
      if(arr.length===2){arr[0].disabled=cur===0;arr[1].disabled=cur===slides.length-1;}
    }
    track.addEventListener('scroll',function(){if(!raf)raf=requestAnimationFrame(mark);},{passive:true});
    window.addEventListener('resize',function(){if(cur>=0)go(cur,true);});
    tabs.forEach(function(t,k){t.addEventListener('click',function(e){e.preventDefault();go(k);});});
    arr.forEach(function(b){b.addEventListener('click',function(){go(cur+(+b.getAttribute('data-dir')));});});
    track.addEventListener('keydown',function(e){
      if(e.target!==track)return;
      if(e.key==='ArrowRight'){e.preventDefault();go(cur+1);}else if(e.key==='ArrowLeft'){e.preventDefault();go(cur-1);}
    });
    function fromHash(){
      var id=decodeURIComponent(location.hash.slice(1));
      for(var k=0;k<slides.length;k++)if(slides[k].id===id){go(k,true);car.scrollIntoView({block:'start'});return;}
    }
    mark();fromHash();window.addEventListener('hashchange',fromHash);car.classList.add('ready');
  });

  /* index rows (style c): open from a link, and wake the rows inside when opened */
  function openFromHash(){
    var id=decodeURIComponent(location.hash.slice(1)),el=id&&document.getElementById(id);
    if(el&&el.tagName==='DETAILS')el.open=true;
  }
  document.querySelectorAll('details').forEach(function(d){
    d.addEventListener('toggle',function(){d.querySelectorAll('.rail').forEach(function(r){if(r._upd)r._upd();});});
  });
  openFromHash();window.addEventListener('hashchange',openFromHash);

  /* black and white until looked at: on touch screens, colour comes on mid-screen */
  if(window.matchMedia&&window.matchMedia('(hover: none)').matches&&'IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){e.target.classList.toggle('lit',e.isIntersecting);});},{rootMargin:'-32% 0px -32% 0px'});
    document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
  }

  /* name list (style c): the picture follows the name you point at */
  var peek=document.getElementById('peek-img');
  if(peek){
    var on=null;
    document.querySelectorAll('.name').forEach(function(n){
      function show(){
        if(on)on.classList.remove('on');on=n;n.classList.add('on');
        peek.src='img/'+n.getAttribute('data-cover')+'-m.webp';
      }
      n.addEventListener('pointerenter',show);n.addEventListener('focus',show);
    });
  }

  /* lightbox for any set: a garment (p0..: its model photos, then the groups in it)
     or a group (g0..) */
  var lb=document.getElementById('lb'),lbImg=document.getElementById('lb-img'),cap=document.getElementById('lb-cap');
  var set=null,i=0,lastFocus=null;
  function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');}
  function src(im){return im.s||'img/'+im.b+'-l.webp';}
  function warmLb(k){var im=set.imgs[k];if(im)(new Image()).src=src(im);}
  function show(){
    var im=set.imgs[i],n=set.imgs.length,pos=' · '+(i+1)+' / '+n;
    lbImg.src=src(im);
    if(im.s){
      lbImg.alt=set.t+' fra Frostline på modell'+(im.c?', '+im.c.toLowerCase():'');
      cap.innerHTML='<b>'+esc(set.t)+'</b>'+(im.c?' · '+esc(im.c):'')+pos;
    }else if(set.k==='c'){
      lbImg.alt='Russegruppa '+set.t+' i '+set.w.toLowerCase()+' fra Frostline';
      cap.innerHTML='<b>'+esc(set.t)+'</b> · '+esc(set.w)+(n>1?pos:'');
    }else{
      var who=im.g||set.t;
      lbImg.alt='Russegruppa '+who+(set.k==='p'?' i '+set.t.toLowerCase():' i klær')+' fra Frostline';
      cap.innerHTML='<b>'+esc(who)+'</b>'+(set.k==='p'?' · '+esc(set.t):'')+pos;
    }
    warmLb((i+1)%n);warmLb((i-1+n)%n);
  }
  function open(key,k){
    set=D.s[key];if(!set)return;i=k||0;lastFocus=document.activeElement;
    lb.hidden=false;document.body.classList.add('lb-open');show();lb.querySelector('.lb-close').focus();
  }
  function close(){lb.hidden=true;document.body.classList.remove('lb-open');lbImg.removeAttribute('src');if(lastFocus&&lastFocus.focus)lastFocus.focus();}
  function next(){i=(i+1)%set.imgs.length;show();}
  function prev(){i=(i-1+set.imgs.length)%set.imgs.length;show();}
  document.addEventListener('click',function(e){
    var b=e.target.closest('[data-s]');
    if(b){e.preventDefault();open(b.getAttribute('data-s'),+b.getAttribute('data-i'));return;}
    if(lb.hidden)return;
    if(e.target.closest('.lb-close')){close();return;}
    if(e.target.closest('.lb-next')){next();return;}
    if(e.target.closest('.lb-prev')){prev();return;}
    if(e.target===lb||e.target.classList.contains('lb-fig'))close();
  });
  document.addEventListener('keydown',function(e){
    if(lb.hidden)return;
    if(e.key==='Escape')close();else if(e.key==='ArrowRight')next();else if(e.key==='ArrowLeft')prev();
  });
  var sx=0,sy=0,sw=false;
  lb.addEventListener('touchstart',function(e){var t=e.touches[0];sx=t.clientX;sy=t.clientY;sw=true;},{passive:true});
  lb.addEventListener('touchend',function(e){
    if(!sw)return;sw=false;var t=e.changedTouches[0],dx=t.clientX-sx,dy=t.clientY-sy;
    if(Math.abs(dx)>40&&Math.abs(dx)>Math.abs(dy)*1.3){dx<0?next():prev();}
    else if(dy>90&&Math.abs(dy)>Math.abs(dx)*1.3){close();}
  },{passive:true});
  var m=/^#([gp])(\d+)-(\d+)$/.exec(location.hash);
  if(m&&D.s[m[1]+m[2]]&&D.s[m[1]+m[2]].imgs[+m[3]])open(m[1]+m[2],+m[3]);
})();
