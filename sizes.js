/* The size guide (build.py size_guide, sizes.css). Pointing at a column or at a letter on the
   photo lights that measurement up on both (on bukse and shorts on both cuts at once; a tap on
   the letter or the column head keeps it lit), and a tapped size row stays lit so it reads
   across on a phone. On /storrelser the row of garments picks the guide that shows
   (storrelser#bukse); on a garment page the Størrelser link opens the garment's guide in a
   sheet. */
(function(){
  function each(list,fn){Array.prototype.forEach.call(list,fn);}

  function guide(root){
    var pinned=null;
    function light(k){
      each(root.querySelectorAll('.sg-svg'),function(svg){
        svg.classList.toggle('hl',!!k);
        each(svg.querySelectorAll('.sg-m'),function(m){m.classList.toggle('on',m.getAttribute('data-k')===k);});
      });
      each(root.querySelectorAll('.sg-t [data-k]'),function(c){c.classList.toggle('on',c.getAttribute('data-k')===k);});
    }
    root.addEventListener('pointerover',function(e){
      if(e.pointerType!=='mouse')return;
      var el=e.target.closest('[data-k]');
      light(el?el.getAttribute('data-k'):pinned);
    });
    root.addEventListener('pointerleave',function(e){if(e.pointerType==='mouse')light(pinned);});
    root.addEventListener('click',function(e){
      var head=e.target.closest('thead [data-k], .sg-m');
      if(head){
        var k=head.getAttribute('data-k');
        pinned=pinned===k?null:k;light(pinned);return;
      }
      var tr=e.target.closest('tbody tr');
      if(!tr||tr.classList.contains('sg-gh'))return;
      var on=!tr.classList.contains('sel');
      each(root.querySelectorAll('.sg-t tbody tr'),function(r){r.classList.remove('sel');});
      tr.classList.toggle('sel',on);
    });
  }
  each(document.querySelectorAll('.sg'),guide);

  /* /storrelser: one garment at a time, picked in the row or by the address */
  var pick=document.querySelector('.sg-pick');
  if(pick){
    var secs=document.querySelectorAll('.sg-g'),links=pick.querySelectorAll('.sg-pk'),ids=[];
    each(secs,function(s){ids.push(s.getAttribute('data-g'));});
    var show=function(g,glide){
      each(secs,function(s){s.hidden=s.getAttribute('data-g')!==g;});
      each(links,function(a){
        var on=a.getAttribute('data-g')===g;a.setAttribute('aria-current',on?'true':'false');
        if(on){ /* keep the picked garment in view in the row */
          var r=a.getBoundingClientRect(),p=pick.getBoundingClientRect();
          if(r.left<p.left+16||r.right>p.right-16)pick.scrollBy({left:r.left-p.left-(p.width-r.width)/2,behavior:glide?'smooth':'auto'});
        }
      });
    };
    /* #bukse, and the older #bukse-dame, open the garment */
    var fromHash=function(){
      var h=decodeURIComponent(location.hash.slice(1)).toLowerCase(),best='';
      ids.forEach(function(g){if((h===g||h.indexOf(g+'-')===0)&&g.length>best.length)best=g;});
      show(best||ids[0],false);
    };
    each(links,function(a){
      a.addEventListener('click',function(e){
        if(e.metaKey||e.ctrlKey||e.shiftKey||e.button)return;
        e.preventDefault();
        var g=a.getAttribute('data-g');show(g,true);
        try{history.replaceState(null,'','#'+g);}catch(x){}
      });
    });
    fromHash();
    window.addEventListener('hashchange',fromHash);
  }

  /* a garment page: the Størrelser link opens the guide in a sheet (and goes to /storrelser
     where the browser has no dialog) */
  var dlg=document.getElementById('sg-dlg');
  if(dlg&&typeof dlg.showModal==='function'){
    each(document.querySelectorAll('[data-sg-open]'),function(a){
      a.addEventListener('click',function(e){
        if(e.metaKey||e.ctrlKey||e.shiftKey||e.button)return;
        e.preventDefault();
        dlg.showModal();document.body.classList.add('sg-open');
      });
    });
    dlg.addEventListener('close',function(){document.body.classList.remove('sg-open');});
    dlg.addEventListener('click',function(e){if(e.target===dlg)dlg.close();});
    dlg.querySelector('.sg-x').addEventListener('click',function(){dlg.close();});
    /* the page's arrow keys step through its photos; not from inside the sheet */
    dlg.addEventListener('keydown',function(e){e.stopPropagation();});
  }
})();
