(function(){
  var data=JSON.parse(document.getElementById('data').textContent);
  var lb=document.getElementById('lb'),img=document.getElementById('lb-img'),cap=document.getElementById('lb-cap');
  var g=0,i=0,lastFocus=null;
  function src(im,size){return 'img/'+im.b+'-'+size+'.webp';}
  function preload(gi,ii){var im=data[gi].imgs[ii];if(im){var p=new Image();p.src=src(im,'l');}}
  function show(){
    var grp=data[g],im=grp.imgs[i];
    img.src=src(im,'l');img.alt='Russegruppa '+grp.name+' i klær fra Frostline';
    cap.innerHTML='<b>'+grp.name.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</b> · '+(i+1)+' / '+grp.imgs.length;
    preload(g,(i+1)%grp.imgs.length);preload(g,(i-1+grp.imgs.length)%grp.imgs.length);
  }
  function open(gi,ii){g=gi;i=ii;lastFocus=document.activeElement;lb.hidden=false;document.body.classList.add('lb-open');show();lb.querySelector('.lb-close').focus();}
  function close(){lb.hidden=true;document.body.classList.remove('lb-open');img.removeAttribute('src');if(lastFocus&&lastFocus.focus)lastFocus.focus();}
  function next(){i=(i+1)%data[g].imgs.length;show();}
  function prev(){i=(i-1+data[g].imgs.length)%data[g].imgs.length;show();}
  document.addEventListener('click',function(e){
    var b=e.target.closest('[data-g]');if(b){open(+b.getAttribute('data-g'),+b.getAttribute('data-i'));return;}
    if(lb.hidden)return;
    if(e.target.closest('.lb-close')){close();return;}
    if(e.target.closest('.lb-next')){next();return;}
    if(e.target.closest('.lb-prev')){prev();return;}
    if(e.target===lb||e.target.classList.contains('lb-fig')){close();}
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
  var m=/^#g(\d+)-(\d+)$/.exec(location.hash);
  if(m&&data[+m[1]]&&data[+m[1]].imgs[+m[2]])open(+m[1],+m[2]);
})();
