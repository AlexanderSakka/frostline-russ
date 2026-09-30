/* The size guide (build.py size_guide, sizes.css). In every guide Unisex / Dame switch the
   photo and the table; pointing at a column or at a letter on the photo lights that
   measurement up on both (a tap on the letter or the column head keeps it lit), and a tapped
   size row stays lit so it reads across on a phone. On /storrelser the row of garments picks
   the guide that shows (storrelser#bukse-dame opens the women's trousers); on a garment page
   the Størrelser link opens the garment's guide in a sheet, in the cut the page shows. */
(function(){
  function each(list,fn){Array.prototype.forEach.call(list,fn);}

  function guide(root){
    var pills=root.querySelectorAll('.sg-pill'),pinned=null;
    function light(k){
      var svg=root.querySelector('.sg-fig:not([hidden]) .sg-svg'),t=root.querySelector('.sg-t:not([hidden])');
      if(svg){
        svg.classList.toggle('hl',!!k);
        each(svg.querySelectorAll('.sg-m'),function(m){m.classList.toggle('on',m.getAttribute('data-k')===k);});
      }
      if(t)each(t.querySelectorAll('[data-k]'),function(c){c.classList.toggle('on',c.getAttribute('data-k')===k);});
    }
    function cut(k){
      var parts=root.querySelectorAll('[data-sg-cut]'),has=false;
      each(parts,function(el){if(el.getAttribute('data-sg-cut')===k)has=true;});
      if(!has)return false;
      each(parts,function(el){el.hidden=el.getAttribute('data-sg-cut')!==k;});
      each(pills,function(b){b.setAttribute('aria-checked',b.getAttribute('data-cut')===k?'true':'false');});
      light(pinned);
      return true;
    }
    each(pills,function(b){
      b.addEventListener('click',function(){
        var k=b.getAttribute('data-cut');
        if(cut(k))root.dispatchEvent(new CustomEvent('sg-cut',{bubbles:true,detail:k}));
      });
    });
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
      if(!tr)return;
      var on=!tr.classList.contains('sel');
      each(tr.parentNode.children,function(r){r.classList.remove('sel');});
      tr.classList.toggle('sel',on);
    });
    root.sgCut=cut;
  }
  each(document.querySelectorAll('.sg'),guide);

  /* /storrelser: one garment at a time, picked in the row or by the address */
  var pick=document.querySelector('.sg-pick');
  if(pick){
    var secs=document.querySelectorAll('.sg-g'),links=pick.querySelectorAll('.sg-pk'),ids=[];
    each(secs,function(s){ids.push(s.getAttribute('data-g'));});
    var show=function(g,k,glide){
      each(secs,function(s){
        var on=s.getAttribute('data-g')===g;s.hidden=!on;
        var gd=s.querySelector('.sg');
        if(on&&k&&gd&&gd.sgCut)gd.sgCut(k);
      });
      each(links,function(a){
        var on=a.getAttribute('data-g')===g;a.setAttribute('aria-current',on?'true':'false');
        if(on){ /* keep the picked garment in view in the row */
          var r=a.getBoundingClientRect(),p=pick.getBoundingClientRect();
          if(r.left<p.left+16||r.right>p.right-16)pick.scrollBy({left:r.left-p.left-(p.width-r.width)/2,behavior:glide?'smooth':'auto'});
        }
      });
    };
    var fromHash=function(){
      var h=decodeURIComponent(location.hash.slice(1)).toLowerCase(),best='';
      ids.forEach(function(g){if((h===g||h.indexOf(g+'-')===0)&&g.length>best.length)best=g;});
      if(best)show(best,h.slice(best.length+1)||null,false);else show(ids[0],null,false);
    };
    each(links,function(a){
      a.addEventListener('click',function(e){
        if(e.metaKey||e.ctrlKey||e.shiftKey||e.button)return;
        e.preventDefault();
        var g=a.getAttribute('data-g');show(g,null,true);
        try{history.replaceState(null,'','#'+g);}catch(x){}
      });
    });
    /* the address follows the cut too, so a link to the women's table can be copied */
    document.addEventListener('sg-cut',function(e){
      var sec=e.target.closest('.sg-g');if(!sec)return;
      var first=sec.querySelector('.sg-pill'),k=e.detail;
      try{history.replaceState(null,'','#'+sec.getAttribute('data-g')+(first&&first.getAttribute('data-cut')===k?'':'-'+k));}catch(x){}
    });
    fromHash();
    window.addEventListener('hashchange',fromHash);
  }

  /* a garment page: the Størrelser link opens the guide in a sheet (and goes to /storrelser
     where the browser has no dialog) */
  var dlg=document.getElementById('sg-dlg');
  if(dlg&&typeof dlg.showModal==='function'){
    var gd=dlg.querySelector('.sg');
    each(document.querySelectorAll('[data-sg-open]'),function(a){
      a.addEventListener('click',function(e){
        if(e.metaKey||e.ctrlKey||e.shiftKey||e.button)return;
        e.preventDefault();
        var on=document.querySelector('.pp-pill[aria-checked="true"]');
        if(on&&gd&&gd.sgCut)gd.sgCut(on.getAttribute('data-k'));
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
