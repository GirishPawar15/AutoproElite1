 // Navbar toggle and scroll behavior
    (function(){
      const toggle=document.querySelector('.nav-toggle');
      const menu=document.querySelector('.nav-menu');
      const nav=document.querySelector('.main-nav');
      if(toggle&&menu){toggle.addEventListener('click',()=>{toggle.classList.toggle('active');menu.classList.toggle('active');});}
      window.addEventListener('scroll',()=>{if(window.scrollY>10) nav.classList.add('scrolled'); else nav.classList.remove('scrolled');});
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
    function basePartCost(area){
      switch(area){
        case 'bumper': return 300;
        case 'door': return 450;
        case 'hood': return 400;
        case 'windshield': return 350;
        case 'engine': return 800;
        case 'suspension': return 500;
        case 'electrical': return 420;
        case 'paint': return 250;
        default: return 300;
      }
    }

    function severityMultiplier(sev){
      return sev==='minor'?0.8:sev==='moderate'?1.2:1.8;
    }

    function vehicleAdj(type){
      return type==='SUV'?1.15:type==='Hatchback'?1.05:1.0;
    }

    function drivableAdj(d){
      return d==='no'?1.1:1.0;
    }

    function estimate(){
      const type=document.getElementById('vehicleType').value;
      const year=+document.getElementById('year').value;
      const area=document.getElementById('area').value;
      const sev=document.getElementById('severity').value;
      const dr=document.getElementById('drivable').value;
      const labor=+document.getElementById('labor').value||80;

      // Guard: require real selections for the main dropdowns
      if(!type || !area || !sev || !dr || !year){
        document.getElementById('price').textContent = '--';
        document.getElementById('breakdown').textContent = 'Please select Vehicle Type, Damage Area, Severity, and Drivable to see an estimate.';
        document.getElementById('questions').classList.add('hidden');
        return;
      }

      const part=basePartCost(area);
      const sevMul=severityMultiplier(sev);
      const vAdj=vehicleAdj(type);
      const dAdj=drivableAdj(dr);

      let laborHours = area==='engine'?6: area==='suspension'?4: area==='door'?3: area==='windshield'?2.5: area==='paint'?2.5: 2;

      let partsCost = part*sevMul*vAdj*dAdj;
      let paintCost = (area==='door'||area==='hood'||area==='bumper'||area==='paint') ? 180*sevMul : 0;

      // Follow-up answers influence: warning lights (diagnostics), airbag (inflators/modules), leak (fluids/hoses)
      const warn = document.getElementById('warnSel') ? document.getElementById('warnSel').value : 'no';
      const airbag = document.getElementById('airbagSel') ? document.getElementById('airbagSel').value : 'no';
      const leak = document.getElementById('leakSel') ? document.getElementById('leakSel').value : 'no';

      // Apply adjustments
      if(warn==='yes'){
        partsCost *= 1.05;           // diagnostics and sensors
        laborHours += 0.5;
      }
      if(airbag==='yes'){
        partsCost += 1200;           // airbag module/cover typical baseline
        laborHours += 4;             // dash/steering wheel work
      }
      if(leak==='yes'){
        partsCost += 200;            // seals/fluids
        laborHours += 1;
      }

      // Age adjustment (older cars sometimes cheaper parts but more labor/time variability)
      const age = Math.max(0, 2025 - year);
      const ageAdj = age>10 ? 0.95 : 1.0;
      partsCost *= ageAdj;

      // Recompute labor cost after any hour adjustments
      const laborCost = laborHours*labor;

      const subtotal = partsCost + laborCost + paintCost;
      const tax = subtotal * 0.08;
      const total = subtotal + tax;

      const low = Math.round(total*0.9);
      const high = Math.round(total*1.15);

      document.getElementById('price').textContent = `₹${Number(low).toLocaleString('en-IN')} - ₹${Number(high).toLocaleString('en-IN')}`;
      document.getElementById('breakdown').innerHTML = `
        Parts: ₹${Number(Math.round(partsCost)).toLocaleString('en-IN')} • Labor (${laborHours.toFixed(1)}h @ ₹${Number(labor).toLocaleString('en-IN')}/h): ₹${Number(Math.round(laborHours*labor)).toLocaleString('en-IN')}${paintCost?` • Paint: ₹${Number(Math.round(paintCost)).toLocaleString('en-IN')}`:''} • Tax: ₹${Number(Math.round(tax)).toLocaleString('en-IN')}<br>
        ${warn==='yes'?'• Includes diagnostics for warning lights':''} ${airbag==='yes'?'• Airbag system costs included':''} ${leak==='yes'?'• Leak inspection/materials included':''}`.trim();

      document.getElementById('questions').classList.remove('hidden');
    }

    document.getElementById('estimateBtn').addEventListener('click', estimate);

    // Auto-recalculate when any input changes (including follow-up selects)
    const recalcSelectors = [
      '#vehicleType', '#year', '#area', '#severity', '#drivable', '#labor',
      '#warnSel', '#airbagSel', '#leakSel'
    ];
    recalcSelectors.forEach(sel => {
      document.querySelectorAll(sel).forEach(el => {
        const evt = el.tagName === 'INPUT' && el.type === 'number' ? 'input' : 'change';
        el.addEventListener(evt, estimate);
      });
    });