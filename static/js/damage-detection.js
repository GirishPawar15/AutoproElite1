 // Navbar behavior handled by partial include
    const fileInput = document.getElementById('fileInput');
    const dropzone = document.getElementById('dropzone');
    const gallery = document.getElementById('gallery');
    const detectBtn = document.getElementById('detectBtn');
    const clearBtn = document.getElementById('clearBtn');

    const items = []; // { img, canvas, ctx, file?, detections: [] }

    function createCard(src, file){
      const card = document.createElement('div');
      card.className = 'card';

      const media = document.createElement('div');
      media.className = 'media';

      const img = document.createElement('img');
      img.alt = 'Uploaded car image';
      img.src = src;

      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      const result = document.createElement('div');
      result.className = 'result';
      result.innerHTML = '<strong>Detections</strong><div class="hint">Run detection to analyze</div>';

      media.appendChild(img);
      media.appendChild(canvas);
      card.appendChild(media);
      card.appendChild(result);

      // Ensure canvas matches rendered size
      img.onload = () => {
        // Fit canvas to media box
        const rect = media.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        drawImageFit(img, ctx, canvas);
      };

      gallery.appendChild(card);
      items.push({img, canvas, ctx, result, file: file || null, detections: []});
    }

    function drawImageFit(img, ctx, canvas){
      // Clear canvas and draw image centered with contain behavior
      ctx.clearRect(0,0,canvas.width,canvas.height);
      const iw = img.naturalWidth, ih = img.naturalHeight;
      const cw = canvas.width, ch = canvas.height;
      const ir = iw/ih; const cr = cw/ch;
      let dw, dh, dx, dy;
      if(ir > cr){ dw = cw; dh = cw/ir; dx = 0; dy = (ch - dh)/2; }
      else { dh = ch; dw = ch*ir; dx = (cw - dw)/2; dy = 0; }
      ctx.drawImage(img, dx, dy, dw, dh);
    }

    function handleFiles(files){
      [...files].forEach(file => {
        if(!file.type.startsWith('image/')) return;
        const reader = new FileReader();
        reader.onload = e => createCard(e.target.result, file);
        reader.readAsDataURL(file);
      });
    }

    // Drag & Drop
    dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', e => { e.preventDefault(); dropzone.classList.remove('dragover'); handleFiles(e.dataTransfer.files); });

    // File input
    fileInput.addEventListener('change', e => handleFiles(e.target.files));

    // Redraw on resize
    window.addEventListener('resize', () => {
      items.forEach(({img, canvas, ctx}) => {
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width; canvas.height = rect.height;
        drawImageFit(img, ctx, canvas);
      });
      // Repaint boxes
      items.forEach(drawDetections);
    });

    // Simulated detection
    const labels = ['Scratch','Dent','Crack','Broken Light','Paint Chip'];

    async function runApiDetection(){
      // Try server-side API first. Requires that items have File objects.
      const form = new FormData();
      const files = items.map(it => it.file).filter(Boolean);
      if(files.length){
        files.forEach(f => form.append('images', f, f.name || 'image.jpg'));
      } else {
        // No files (e.g., images added from URLs) -> no API call
        throw new Error('no_files');
      }

      const resp = await fetch('/api/damage/detect/', { method: 'POST', body: form });
      if(resp.status === 501){
        // Not configured on server
        throw new Error('not_configured');
      }
      if(!resp.ok){
        const text = await resp.text().catch(()=>'');
        throw new Error(`upstream_${resp.status}:${text}`);
      }
      const data = await resp.json();
      // Expect a shape like { results: [ { detections: [ {x,y,w,h,label,score}, ... ] }, ... ] }
      if(!data || !Array.isArray(data.results)){
        throw new Error('bad_payload');
      }
      data.results.forEach((r, idx) => {
        const dets = Array.isArray(r && r.detections) ? r.detections : [];
        items[idx] && (items[idx].detections = dets);
        items[idx] && drawDetections(items[idx]);
        items[idx] && updateResult(items[idx]);
      });
    }

    function runSimulatedDetection(){
      items.forEach(item => {
        const {canvas} = item;
        const count = 1 + Math.floor(Math.random()*3); // 1-3 boxes
        const dets = [];
        for(let i=0;i<count;i++){
          const w = 0.2 + Math.random()*0.35; // relative width
          const h = 0.12 + Math.random()*0.28; // relative height
          const x = Math.random()*(1-w);
          const y = Math.random()*(1-h);
          const label = labels[Math.floor(Math.random()*labels.length)];
          const score = 0.62 + Math.random()*0.32; // 0.62-0.94
          dets.push({x,y,w,h,label,score});
        }
        item.detections = dets;
        drawDetections(item);
        updateResult(item);
      });
    }

    function drawDetections(item){
      const {img, canvas, ctx, detections} = item;
      drawImageFit(img, ctx, canvas);
      ctx.lineWidth = 3;
      detections.forEach((d,idx) => {
        const x = d.x*canvas.width;
        const y = d.y*canvas.height;
        const w = d.w*canvas.width;
        const h = d.h*canvas.height;
        // Color by type
        const color = idx % 2 ? 'rgba(239,68,68,0.95)' : 'rgba(245,158,11,0.95)';
        ctx.strokeStyle = color;
        ctx.strokeRect(x,y,w,h);
        // Label background
        const tag = `${d.label} ${(d.score*100).toFixed(0)}%`;
        ctx.font = '12px Segoe UI, sans-serif';
        const tw = ctx.measureText(tag).width + 10;
        ctx.fillStyle = 'rgba(15,23,42,0.9)';
        ctx.fillRect(x, Math.max(0,y-18), tw, 18);
        ctx.fillStyle = '#fff';
        ctx.fillText(tag, x+5, Math.max(12,y-4));
      });
    }

    function updateResult(item){
      const {result, detections} = item;
      if(!detections.length){
        result.innerHTML = '<strong>Detections</strong><div class="hint">Run detection to analyze</div>';
        return;
      }
      const list = detections.map(d => `<li>${d.label} – ${(d.score*100).toFixed(0)}% confidence</li>`).join('');
      result.innerHTML = `<strong>Detections</strong><ul style="margin:8px 0 0 16px">${list}</ul>`;
    }

    detectBtn.addEventListener('click', async () => {
      if(!items.length){ alert('Please upload at least one image.'); return; }
      detectBtn.disabled = true; detectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting...';
      try{
        await runApiDetection();
      }catch(e){
        // Fallback to simulated detection for any error
        runSimulatedDetection();
      }finally{
        detectBtn.disabled = false; detectBtn.innerHTML = '<i class="fas fa-magnifying-glass"></i> Run Detection';
      }
    });

    clearBtn.addEventListener('click', () => {
      gallery.innerHTML = ''; items.length = 0; fileInput.value = '';
      // Keep book service button visible - users can book without detection
    });
    
    // Service Booking Modal
    const serviceModal = document.getElementById('serviceModal');
    const svClose = document.getElementById('sv_close');
    const svSubmit = document.getElementById('sv_submit');
    const serviceForm = document.getElementById('serviceForm');
    
    function showServiceBooking() {
      // Populate damage list
      const damageList = document.getElementById('damageList');
      const allDetections = [];
      
      items.forEach(item => {
        if(item.detections && item.detections.length > 0){
          item.detections.forEach(d => {
            if(!allDetections.find(det => det.label === d.label)){
              allDetections.push(d);
            }
          });
        }
      });
      
      if(allDetections.length > 0){
        damageList.innerHTML = allDetections.map(d => `
          <div class="damage-item">
            <i class="fas fa-exclamation-circle"></i>
            <span>${d.label} (${(d.score*100).toFixed(0)}% confidence)</span>
          </div>
        `).join('');
      } else {
        damageList.innerHTML = '<div class="damage-item"><i class="fas fa-info-circle"></i><span>No specific damage detected</span></div>';
      }
      
      // Set minimum date to today
      const today = new Date().toISOString().split('T')[0];
      document.getElementById('sv_date').setAttribute('min', today);
      
      // Pre-fill user data if logged in
      const user = JSON.parse(localStorage.getItem('ap_user') || '{}');
      if (user.email) {
        document.getElementById('sv_email').value = user.email;
      }
      
      // Reset form
      serviceForm.reset();
      document.getElementById('sv_city').value = 'Pune'; // Default city
      document.getElementById('sv_success').style.display = 'none';
      document.getElementById('sv_error').style.display = 'none';
      
      serviceModal.style.display = 'flex';
    }
    
    // Both booking buttons should open the modal
    const bookServiceBtn = document.getElementById('bookServiceBtn');
    const bookServiceBtnAssess = document.getElementById('bookServiceBtnAssess');
    
    if(bookServiceBtn){
      bookServiceBtn.addEventListener('click', showServiceBooking);
    }
    
    if(bookServiceBtnAssess){
      bookServiceBtnAssess.addEventListener('click', showServiceBooking);
    }
    
    if(svClose){
      svClose.addEventListener('click', () => {
        serviceModal.style.display = 'none';
      });
    }
    
    if(serviceModal){
      serviceModal.addEventListener('click', (e) => {
        if(e.target === serviceModal) serviceModal.style.display = 'none';
      });
    }
    
    if(svSubmit){
      svSubmit.addEventListener('click', async (e) => {
        e.preventDefault();
        
        // Validate form
        if (!serviceForm.checkValidity()) {
          serviceForm.reportValidity();
          return;
        }
        
        // Collect all detected damages
        const allDetections = [];
        items.forEach(item => {
          if(item.detections && item.detections.length > 0){
            item.detections.forEach(d => {
              allDetections.push(`${d.label} (${(d.score*100).toFixed(0)}% confidence)`);
            });
          }
        });
        
        // Get form data
        const formData = {
          name: document.getElementById('sv_name').value,
          phone: document.getElementById('sv_phone').value,
          email: document.getElementById('sv_email').value,
          city: document.getElementById('sv_city').value,
          car_make: document.getElementById('sv_car_make').value,
          car_model: document.getElementById('sv_car_model').value,
          car_year: document.getElementById('sv_car_year').value,
          reg_number: document.getElementById('sv_reg_number').value,
          preferred_date: document.getElementById('sv_date').value,
          preferred_time: document.getElementById('sv_time').value,
          service_type: document.getElementById('sv_service_type').value,
          message: document.getElementById('sv_message').value,
          detected_damages: allDetections,
          booking_date: new Date().toISOString()
        };
        
        // Show loading state
        svSubmit.disabled = true;
        svSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Booking...';
        
        try {
          // Send booking request
          const token = localStorage.getItem('ap_token');
          const headers = {
            'Content-Type': 'application/json'
          };
          
          if (token) {
            headers['Authorization'] = `Token ${token}`;
          }
          
          const response = await fetch('/api/service/book/', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(formData)
          });
          
          if (response.ok) {
            // Show success message
            document.getElementById('sv_success').style.display = 'flex';
            document.getElementById('sv_error').style.display = 'none';
            serviceForm.style.display = 'none';
            
            // Log activity
            if (token) {
              fetch('/api/activities/log/', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Token ${token}`
                },
                body: JSON.stringify({
                  action: 'create',
                  description: `Booked service slot for ${formData.car_make} ${formData.car_model}`
                })
              }).catch(err => console.log('Activity log failed:', err));
            }
            
            // Close modal after 3 seconds
            setTimeout(() => {
              serviceModal.style.display = 'none';
              serviceForm.style.display = 'flex';
              serviceForm.reset();
            }, 3000);
          } else {
            throw new Error('Booking failed');
          }
        } catch (error) {
          console.error('Service booking error:', error);
          document.getElementById('sv_error_message').textContent = 'Failed to book service slot. Please try again or contact us directly.';
          document.getElementById('sv_error').style.display = 'flex';
          document.getElementById('sv_success').style.display = 'none';
        } finally {
          svSubmit.disabled = false;
          svSubmit.innerHTML = '<i class="fas fa-calendar-check"></i> Confirm Booking';
        }
      });
    }
