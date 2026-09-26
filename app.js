(function(){
  var D=JSON.parse(document.getElementById('data').textContent);

  /* top bar gets its hairline once the page moves */
  var bar=document.querySelector('.bar');
  function onScroll(){bar.classList.toggle('scrolled',window.scrollY>4);}
  onScroll();window.addEventListener('scroll',onScroll,{passive:true});

  /* studio: side, colour and cut for each garment */
  function colorName(c){for(var k=0;k<D.c.length;k++)if(D.c[k][0]===c)return D.c[k][1];return c;}
  function studio(root){
    var P=D.p[+root.getAttribute('data-p')];
    var stage=root.querySelector('.stage'),ctrl=root.querySelector('.ctrl');
    if(!P||!stage||!ctrl)return;
    var img=stage.querySelector('img'),sws=ctrl.querySelector('.swatches');
    var st={cut:P.cuts[0][0],view:'front',color:D.c[0][0]};
    function cutLabel(c){for(var k=0;k<P.cuts.length;k++)if(P.cuts[k][0]===c)return P.cuts[k][1];return '';}
    function file(s){return 'img/p/'+s.cut+'-'+(s.view==='life'?'life':s.color+'-'+s.view);}
    function alt(){
      if(st.view==='life')return P.name+' fra Frostline på modell';
      var lab=cutLabel(st.cut),snitt=lab?' i '+(lab==='Unisex'?'unisex-snitt':'damesnitt'):'';
      return colorName(st.color)+' '+P.lname+snitt+' fra Frostline, '+(st.view==='front'?'forfra':'bakfra');
    }
    function render(){
      var f=file(st),life=st.view==='life';
      img.srcset=f+'-600.webp 600w, '+f+'-1000.webp 1000w';img.src=f+'-1000.webp';img.alt=alt();
      stage.classList.toggle('is-life',life);if(sws)sws.classList.toggle('off',life);
    }
    var warm=false;
    function preload(){
      if(warm)return;warm=true;
      var size=(img.currentSrc||img.src).indexOf('-600.')>-1?'-600.webp':'-1000.webp';
      P.cuts.forEach(function(c){
        D.c.forEach(function(col){['front','back'].forEach(function(v){(new Image()).src=file({cut:c[0],color:col[0],view:v})+size;});});
        (new Image()).src='img/p/'+c[0]+'-life'+size;
      });
    }
    ctrl.addEventListener('pointerenter',preload);ctrl.addEventListener('focusin',preload);
    ctrl.addEventListener('touchstart',preload,{passive:true});
    ctrl.addEventListener('click',function(e){
      var b=e.target.closest('button[data-v]');if(!b)return;
      var grp=b.parentNode;st[grp.getAttribute('data-k')]=b.getAttribute('data-v');
      grp.querySelectorAll('button[data-v]').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});
      render();
    });
  }
  document.querySelectorAll('[data-p]').forEach(studio);

  /* photo rows: arrows on wide screens, swipe everywhere */
  document.querySelectorAll('.worn').forEach(function(w){
    var rail=w.querySelector('.rail'),a=w.querySelectorAll('.arr');
    if(!rail||a.length<2)return;
    function upd(){var max=rail.scrollWidth-rail.clientWidth-2;a[0].disabled=rail.scrollLeft<=2;a[1].disabled=rail.scrollLeft>=max;}
    a.forEach(function(b){b.addEventListener('click',function(){rail.scrollBy({left:(+b.getAttribute('data-dir'))*rail.clientWidth*.9,behavior:'smooth'});});});
    rail.addEventListener('scroll',upd,{passive:true});window.addEventListener('resize',upd);
    rail._upd=upd;upd();
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

  /* lightbox for any set: a garment's photos (p0..) or a group's (g0..) */
  var lb=document.getElementById('lb'),lbImg=document.getElementById('lb-img'),cap=document.getElementById('lb-cap');
  var set=null,i=0,lastFocus=null;
  function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');}
  function src(im){return 'img/'+im.b+'-l.webp';}
  function warmLb(k){var im=set.imgs[k];if(im)(new Image()).src=src(im);}
  function show(){
    var im=set.imgs[i],n=set.imgs.length,who=im.g||set.t;
    lbImg.src=src(im);
    lbImg.alt='Russegruppa '+who+(set.k==='p'?' i '+set.t.toLowerCase():' i klær')+' fra Frostline';
    cap.innerHTML='<b>'+esc(who)+'</b>'+(set.k==='p'?' · '+esc(set.t):'')+' · '+(i+1)+' / '+n;
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
