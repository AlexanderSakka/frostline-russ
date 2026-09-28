/* A garment's own page (<id>.html): the photos in the cut and colour picked (front, back, on
   a model), and on a hoodie or zip hoodie the surname typed, drawn on the back photo while
   it is typed. The print box and the fitting are the school store's preview
   (~/skole/assets/surname-preview.js): the box is a share of the photo, the type is as tall
   as the box and shrinks until a long name fits its width. Dark garments get the name in
   white. The data (cuts, colours, photos) is the #pp-data JSON that build.py writes. */
(function(){
  var el=document.getElementById('pp-data');if(!el)return;
  var P=JSON.parse(el.textContent);
  var stage=document.getElementById('pp-stage'),img=document.getElementById('pp-img'),
      thumbs=document.getElementById('pp-thumbs'),nm=document.getElementById('pp-name'),
      cn=document.getElementById('pp-cn'),sws=document.getElementById('pp-sws'),
      input=document.getElementById('pp-in'),count=document.getElementById('pp-count'),
      pills=[].slice.call(document.querySelectorAll('.pp-pill')),lb=document.getElementById('lb');
  var st={cut:0,col:0,v:0},KEY='frostline-etternavn',ctx=null;
  /* the print box for this garment (build.py NAME_BOX), in % of the photo */
  if(nm&&P.box){['left','top','width','height'].forEach(function(k,i){nm.style[k]=P.box[i]+'%';});}

  function cut(){return P.cuts[st.cut];}
  function col(){return cut().colours[st.col];}
  function views(){
    var c=col(),v=[{t:'front',p:c.front}];
    if(c.back)v.push({t:'back',p:c.back});
    if(cut().model)v.push({t:'model',p:cut().model});
    return v;
  }
  function kind(){return views()[st.v].t;}
  function indexOf(t){var vs=views();for(var k=0;k<vs.length;k++)if(vs[k].t===t)return k;return -1;}

  function show(k){
    var vs=views();st.v=(k+vs.length)%vs.length;
    var v=vs[st.v];
    if(img.getAttribute('src')!==v.p.s){img.srcset=v.p.ss;img.src=v.p.s;}
    img.alt=v.p.alt;
    stage.classList.toggle('is-model',v.t==='model');
    stage.classList.toggle('is-dark',v.t!=='model'&&!!col().dark);
    [].forEach.call(thumbs.children,function(b,i){b.setAttribute('aria-current',i===st.v?'true':'false');});
    paint();
  }
  function drawThumbs(){
    thumbs.innerHTML='';
    views().forEach(function(v,i){
      var b=document.createElement('button');
      b.type='button';b.className='pp-th';b.setAttribute('data-v',i);b.setAttribute('aria-label',v.p.alt);
      var im=document.createElement('img');
      im.src=v.p.ss.split(' ')[0];im.alt='';im.width=120;im.height=120;im.decoding='async';
      b.appendChild(im);thumbs.appendChild(b);
    });
  }
  function drawSwatches(){
    sws.innerHTML='';
    cut().colours.forEach(function(c,i){
      var b=document.createElement('button');
      b.type='button';b.className='pp-sw';b.setAttribute('role','radio');b.setAttribute('data-col',i);
      b.style.setProperty('--c',c.hex);b.setAttribute('aria-label',c.name);
      b.setAttribute('aria-checked',i===st.col?'true':'false');
      sws.appendChild(b);
    });
    cn.textContent=col().name;
  }
  function address(){
    var h=[];if(P.cuts.length>1)h.push(cut().k);h.push(col().k);
    try{history.replaceState(null,'','#'+h.join('-'));}catch(e){}
  }
  /* a new colour or cut keeps you on the back if that is where you were, or if a name is
     typed (the back is the point of it then); otherwise the front */
  function stay(){
    var t=kind(),named=input&&input.value.trim();
    return t==='back'||(named&&t!=='model')?'back':t==='model'?'model':'front';
  }
  function setColour(i){
    var t=stay();st.col=i;drawSwatches();drawThumbs();show(Math.max(0,indexOf(t)));address();
  }
  function setCut(i){
    var t=stay(),k=col().k;st.cut=i;st.col=0;
    cut().colours.forEach(function(c,j){if(c.k===k)st.col=j;});
    pills.forEach(function(b,j){b.setAttribute('aria-checked',j===i?'true':'false');});
    drawSwatches();drawThumbs();show(Math.max(0,indexOf(t)));address();
  }

  /* the surname on the back, and only while the back photo is what is on screen: a browser
     keeps the photo before it up until the new one has loaded, so not before that either */
  function paint(){
    if(!nm)return;
    var on=P.navn&&kind()==='back'&&img.complete&&img.naturalWidth>0;
    nm.hidden=!on;if(!on)return;
    var name=input?input.value.trim().replace(/\s+/g,' ').toUpperCase():'';
    nm.textContent=name||'ETTERNAVN';
    nm.classList.toggle('ph',!name);
    nm.classList.toggle('lt',!!col().dark);
    fit();
  }
  function fit(){
    var w=nm.clientWidth,h=nm.clientHeight;if(!w||!h)return;
    nm.style.fontSize=h+'px';
    var cs=getComputedStyle(nm),t=nm.textContent;
    ctx=ctx||document.createElement('canvas').getContext('2d');
    ctx.font=cs.fontStyle+' '+cs.fontWeight+' '+h+'px '+cs.fontFamily;
    var tw=ctx.measureText(t).width+(parseFloat(cs.letterSpacing)||0)*t.length,lim=w*.98;
    if(tw>lim)nm.style.fontSize=Math.max(6,h*lim/tw)+'px';
  }
  function toBack(){var k=indexOf('back');if(k>=0&&st.v!==k)show(k);}
  if(input){
    try{input.value=(sessionStorage.getItem(KEY)||'').slice(0,18);}catch(e){}
    count.textContent=input.value.length+'/18';
    input.addEventListener('input',function(){
      var up=input.value.toUpperCase();
      if(up!==input.value){var p=input.selectionStart;input.value=up;try{input.setSelectionRange(p,p);}catch(e){}}
      count.textContent=input.value.length+'/18';
      try{sessionStorage.setItem(KEY,input.value);}catch(e){}
      if(kind()!=='back')toBack();else paint();
    });
    input.addEventListener('focus',toBack);
    input.addEventListener('keydown',function(e){if(e.key==='Enter')input.blur();});
  }

  /* picking */
  thumbs.addEventListener('click',function(e){var b=e.target.closest('.pp-th');if(b)show(+b.getAttribute('data-v'));});
  sws.addEventListener('click',function(e){var b=e.target.closest('.pp-sw');if(b)setColour(+b.getAttribute('data-col'));});
  pills.forEach(function(b,i){b.addEventListener('click',function(){setCut(i);});});
  stage.querySelectorAll('.pp-arr').forEach(function(b){b.addEventListener('click',function(){show(st.v+(+b.getAttribute('data-dir')));});});
  document.addEventListener('keydown',function(e){
    if((lb&&!lb.hidden)||e.target===input||e.altKey||e.metaKey||e.ctrlKey)return;
    if(e.key==='ArrowRight')show(st.v+1);else if(e.key==='ArrowLeft')show(st.v-1);
  });
  var sx=0,sy=0,sw=false;
  stage.addEventListener('touchstart',function(e){var t=e.touches[0];sx=t.clientX;sy=t.clientY;sw=true;},{passive:true});
  stage.addEventListener('touchend',function(e){
    if(!sw)return;sw=false;var t=e.changedTouches[0],dx=t.clientX-sx,dy=t.clientY-sy;
    if(Math.abs(dx)>40&&Math.abs(dx)>Math.abs(dy)*1.3)show(st.v+(dx<0?1:-1));
  },{passive:true});
  window.addEventListener('resize',function(){if(nm&&!nm.hidden)fit();});
  img.addEventListener('load',paint);
  /* The name is measured in Bebas Neue, but a browser only fetches a font once some text
     uses it, and the name is hidden until the back is shown. Measured before it arrived, a
     long name was fitted in the much wider fallback face and came out a third too small.
     So ask for it now, and fit again whenever a font finishes loading. */
  if(P.navn&&document.fonts){
    var refit=function(){if(nm&&!nm.hidden)fit();};
    if(document.fonts.load)document.fonts.load('400 40px "Bebas Neue"').then(refit,function(){});
    if(document.fonts.addEventListener)document.fonts.addEventListener('loadingdone',refit);
  }

  /* a link can pick the colour and cut: hoodie#navy, bukse#dame-svart */
  function fromHash(){
    var h=decodeURIComponent(location.hash.slice(1)).split('-');
    P.cuts.forEach(function(c,i){if(c.k&&h.indexOf(c.k)>=0)st.cut=i;});
    st.col=0;cut().colours.forEach(function(c,i){if(h.indexOf(c.k)>=0)st.col=i;});
    pills.forEach(function(b,j){b.setAttribute('aria-checked',j===st.cut?'true':'false');});
    drawSwatches();drawThumbs();show(0);
  }
  fromHash();
  window.addEventListener('hashchange',fromHash);
})();
