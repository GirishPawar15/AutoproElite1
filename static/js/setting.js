const BASE_API = (location.origin && location.origin.startsWith('http')) ? (location.origin.replace(/\/$/, '') + '/api') : 'http://127.0.0.1:8000/api';
    function token(){ return localStorage.getItem('ap_token'); }
    async function apiGet(path){
      const r = await fetch(BASE_API + path, { headers: { 'Accept': 'application/json', 'Authorization': 'Token ' + token() }});
      const j = await r.json().catch(()=>({}));
      if(!r.ok) throw new Error(j.detail || ('HTTP ' + r.status));
      return j;
    }
    async function apiPut(path, data){
      const r = await fetch(BASE_API + path, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Token ' + token() }, body: JSON.stringify(data)});
      const j = await r.json().catch(()=>({}));
      if(!r.ok) throw new Error(j.detail || ('HTTP ' + r.status));
      return j;
    }
    async function uploadImage(file){
      const fd = new FormData(); fd.append('file', file);
      const r = await fetch(BASE_API + '/upload/', { method: 'POST', body: fd });
      const j = await r.json();
      if(!r.ok || !j.url) throw new Error(j.detail || 'Upload failed');
      return j.url;
    }

    function render(data){
      document.getElementById('username').value = data.username || '';
      const img = document.getElementById('avatar_img');
      const hint = document.getElementById('avatar_hint');
      if (data.avatar_url){ img.src = data.avatar_url; img.style.display = 'block'; hint.style.display = 'none'; }
      else { img.style.display = 'none'; hint.style.display = 'inline'; }
    }

    async function load(){
      try{
        if(!token()){ window.location.href = '/login/'; return; }
        const me = await apiGet('/account/me/');
        render(me);
      }catch(e){ document.getElementById('msg').textContent = 'Load failed: ' + e.message; }
    }
    async function save(){
      document.getElementById('msg').textContent = '';
      let avatar_url = undefined;
      const f = document.getElementById('avatar_file').files[0];
      try{
        if (f) avatar_url = await uploadImage(f);
      }catch(e){ document.getElementById('msg').textContent = 'Upload failed: ' + e.message; return; }
      try{
        const payload = { username: document.getElementById('username').value };
        if (avatar_url) payload.avatar_url = avatar_url;
        const res = await apiPut('/account/me/', payload);
        render(res);
        document.getElementById('msg').textContent = 'Settings saved.';
      }catch(e){ document.getElementById('msg').textContent = 'Save failed: ' + e.message; }
    }
    document.addEventListener('DOMContentLoaded', function(){
      load();
      document.getElementById('saveBtn').addEventListener('click', save);
    });
 