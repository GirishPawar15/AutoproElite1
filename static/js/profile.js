    const BASE_API = (location.origin && location.origin.startsWith('http'))
      ? (location.origin.replace(/\/$/, '') + '/api')
      : 'http://127.0.0.1:8000/api';

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

    function setPreview(idPrefix, url){
      const img = document.getElementById(idPrefix + '_preview');
      const a = document.getElementById(idPrefix + '_link');
      if(url){ img.src = url; img.style.display = 'block'; a.href = url; a.style.display = 'inline-block'; }
      else { img.style.display = 'none'; a.style.display = 'none'; }
    }

    function showView(){
      document.getElementById('profileView').style.display = 'block';
      document.getElementById('profileForm').style.display = 'none';
    }
    function showEdit(){
      document.getElementById('profileView').style.display = 'none';
      document.getElementById('profileForm').style.display = 'block';
    }

    function renderView(p){
      const setText = (id, v) => document.getElementById(id).textContent = (v && String(v).trim()) || '-';
      setText('v_full_name', p.full_name);
      setText('v_phone', p.phone);
      setText('v_dl_no', p.driving_license_number);
      setText('v_aadhaar_no', p.aadhar_number);
      setText('v_pan_no', p.pan_number);
      setText('v_car_make', p.car_make);
      setText('v_car_model', p.car_model);
      setText('v_car_year', p.car_year);

      const setImg = (id, url) => {
        const el = document.getElementById(id);
        if (url) { el.src = url; el.style.display = 'block'; }
        else { el.style.display = 'none'; }
      };
      setImg('v_dl_img', p.driving_license_image);
      setImg('v_aadhaar_img', p.aadhar_image);
      setImg('v_pan_img', p.pan_image);
      setImg('v_car_img', p.car_image);
    }

    async function loadProfile(){
      try{
        if(!token()){ window.location.href = '/login/'; return; }
        const p = await apiGet('/profile/me/');
        document.getElementById('full_name').value = p.full_name || '';
        document.getElementById('phone').value = p.phone || '';
        document.getElementById('dl_no').value = p.driving_license_number || '';
        document.getElementById('aadhaar_no').value = p.aadhar_number || '';
        document.getElementById('pan_no').value = p.pan_number || '';
        document.getElementById('car_make').value = p.car_make || '';
        document.getElementById('car_model').value = p.car_model || '';
        document.getElementById('car_year').value = p.car_year || '';
        setPreview('dl', p.driving_license_image || '');
        setPreview('aadhaar', p.aadhar_image || '');
        setPreview('pan', p.pan_image || '');
        setPreview('car', p.car_image || '');
        renderView(p);
        showView();
      }catch(e){
        document.getElementById('msg').textContent = 'Failed to load profile: ' + e.message;
      }
    }

    async function saveProfile(){
      const data = {
        full_name: document.getElementById('full_name').value,
        phone: document.getElementById('phone').value,
        driving_license_number: document.getElementById('dl_no').value,
        aadhar_number: document.getElementById('aadhaar_no').value,
        pan_number: document.getElementById('pan_no').value,
        car_make: document.getElementById('car_make').value,
        car_model: document.getElementById('car_model').value,
        car_year: Number(document.getElementById('car_year').value || 0),
      };
      try{
        const dlFile = document.getElementById('dl_img').files[0];
        if (dlFile) data.driving_license_image = await uploadImage(dlFile);
        const aFile = document.getElementById('aadhaar_img').files[0];
        if (aFile) data.aadhar_image = await uploadImage(aFile);
        const pFile = document.getElementById('pan_img').files[0];
        if (pFile) data.pan_image = await uploadImage(pFile);
        const cFile = document.getElementById('car_img').files[0];
        if (cFile) data.car_image = await uploadImage(cFile);
      }catch(e){
        document.getElementById('msg').textContent = 'Upload failed: ' + e.message;
        return;
      }
      try{
        const saved = await apiPut('/profile/me/', data);
        document.getElementById('msg').textContent = 'Profile saved.';
        setPreview('dl', saved.driving_license_image || '');
        setPreview('aadhaar', saved.aadhar_image || '');
        setPreview('pan', saved.pan_image || '');
        setPreview('car', saved.car_image || '');
        renderView(saved);
        showView();
      }catch(e){
        document.getElementById('msg').textContent = 'Save failed: ' + e.message;
      }
    }

    document.addEventListener('DOMContentLoaded', function(){
      loadProfile();
      document.getElementById('saveBtn').addEventListener('click', saveProfile);
      document.getElementById('editBtn').addEventListener('click', function(){ showEdit(); });
      document.getElementById('cancelBtn').addEventListener('click', function(){ showView(); });
    });
