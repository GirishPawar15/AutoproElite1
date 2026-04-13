 (function(){
      const toggle = document.querySelector('.nav-toggle');
      const menu = document.querySelector('.nav-menu');
      const nav = document.querySelector('.main-nav');
      if(toggle && menu){ toggle.addEventListener('click', ()=>{ toggle.classList.toggle('active'); menu.classList.toggle('active'); }); }
      window.addEventListener('scroll', ()=>{ if(window.scrollY>10) nav.classList.add('scrolled'); else nav.classList.remove('scrolled'); });
      const loginBtn=document.getElementById('loginBtn');
      const signupBtn=document.getElementById('signupBtn');
      const accountBtn=document.getElementById('accountBtn');
      const logoutBtn=document.getElementById('logoutBtn');
      if(loginBtn) loginBtn.onclick=()=>location.href='/login/';
      if(signupBtn) signupBtn.onclick=()=>location.href='/signup/';
      const token = localStorage.getItem('ap_token');
      const loggedIn = !!token;
      if(accountBtn) accountBtn.style.display = loggedIn ? 'inline-flex' : 'none';
      if(logoutBtn) logoutBtn.style.display = loggedIn ? 'inline-flex' : 'none';
      if(loginBtn) loginBtn.style.display = loggedIn ? 'none' : 'inline-flex';
      if(signupBtn) signupBtn.style.display = loggedIn ? 'none' : 'inline-flex';
      if(logoutBtn) logoutBtn.onclick = () => {
        try { localStorage.removeItem('ap_token'); localStorage.removeItem('ap_user'); } catch(e){}
        location.href = '/';
      };
    })();
