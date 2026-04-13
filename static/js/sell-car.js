    // API base (tries same-origin /api, falls back to localhost dev server)
    const BASE_API = (location.origin && location.origin.startsWith('http'))
      ? (location.origin.replace(/\/$/, '') + '/api')
      : 'http://127.0.0.1:8000/api';

    async function apiGet(path){
      try{
        const token = localStorage.getItem('ap_token');
        const r = await fetch(`${BASE_API}${path}`, {
          headers: {
            'Accept': 'application/json',
            ...(token ? { 'Authorization': `Token ${token}` } : {})
          }
        });
        if(!r.ok) throw new Error('HTTP ' + r.status);
        return await r.json();
      }catch(err){
        return null; // signal failure to allow graceful fallback
      }
    }

    async function apiPost(path, data){
      try{
        const token = localStorage.getItem('ap_token');
        const r = await fetch(`${BASE_API}${path}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...(token ? { 'Authorization': `Token ${token}` } : {})
          },
          body: JSON.stringify(data)
        });
        const json = await r.json().catch(()=>({}));
        if(!r.ok) throw new Error((json && json.detail) || 'HTTP ' + r.status);
        return json;
      }catch(err){
        return { __error: true, message: String(err && err.message || err) };
      }
    }

    // Enhanced image upload with multiple file support
    const photos = document.getElementById('photos');
    const preview = document.getElementById('preview');
    let uploadedImageUrls = [];
    
    photos.addEventListener('change', async () => {
      preview.innerHTML = '';
      uploadedImageUrls = [];
      
      const files = [...photos.files].slice(0, 8); // Limit to 8 images
      
      if (files.length === 0) return;
      
      // Show loading state
      preview.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding:20px; color:var(--muted)"><i class="fas fa-spinner fa-spin"></i> Uploading images...</div>';
      
      try {
        // Upload all images
        const formData = new FormData();
        files.forEach(file => {
          formData.append('files', file);
        });
        
        const response = await fetch('/api/upload/', {
          method: 'POST',
          body: formData
        });
        
        if (!response.ok) throw new Error('Upload failed');
        
        const result = await response.json();
        
        // Handle both single and multiple file responses
        const uploadedFiles = result.files || [{ url: result.url, filename: files[0].name }];
        
        // Clear loading and show previews
        preview.innerHTML = '';
        
        uploadedFiles.forEach((fileData, index) => {
          uploadedImageUrls.push(fileData.url);
          
          const container = document.createElement('div');
          container.style.position = 'relative';
          
          const img = document.createElement('img');
          img.src = fileData.url;
          img.style.width = '100%';
          img.style.height = '120px';
          img.style.objectFit = 'cover';
          img.style.borderRadius = '10px';
          img.style.border = '2px solid var(--border)';
          
          // Add remove button
          const removeBtn = document.createElement('button');
          removeBtn.innerHTML = '<i class="fas fa-times"></i>';
          removeBtn.style.cssText = 'position:absolute;top:4px;right:4px;background:rgba(220,38,38,0.9);color:#fff;border:none;border-radius:50%;width:24px;height:24px;cursor:pointer;font-size:12px';
          removeBtn.addEventListener('click', () => {
            uploadedImageUrls.splice(uploadedImageUrls.indexOf(fileData.url), 1);
            container.remove();
            updateHiddenImageField();
          });
          
          // Add primary badge for first image
          if (index === 0) {
            const badge = document.createElement('div');
            badge.textContent = 'Primary';
            badge.style.cssText = 'position:absolute;bottom:4px;left:4px;background:var(--primary);color:#fff;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600';
            container.appendChild(badge);
          }
          
          container.appendChild(img);
          container.appendChild(removeBtn);
          preview.appendChild(container);
        });
        
        updateHiddenImageField();
        
      } catch (error) {
        preview.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding:20px; color:#dc2626"><i class="fas fa-exclamation-triangle"></i> Upload failed. Please try again.</div>';
        console.error('Upload error:', error);
      }
    });
    
    function updateHiddenImageField() {
      // Set the first image as the main img field for backward compatibility
      document.getElementById('img').value = uploadedImageUrls[0] || '';
      // Set all image URLs as JSON array
      document.getElementById('image_urls').value = JSON.stringify(uploadedImageUrls);
    }

    // Draft save and sample list
    const form = document.getElementById('sellForm');
    const drafts = document.getElementById('drafts');

    function renderDraft(d){
      const item = document.createElement('div');
      item.className = 'car-item';
      const img = document.createElement('img');
      img.src = 'https://images.unsplash.com/photo-1549924231-f129b911e442?q=80&w=800&auto=format&fit=crop';
      const box = document.createElement('div');
      box.innerHTML = `<div class="title">${d.make} ${d.model} • ₹${Number(d.price).toLocaleString('en-IN')}</div>
        <div class="meta">${d.year} • ${Number(d.km).toLocaleString()} km • ${d.fuel} • ${d.trans}</div>`;
      item.append(img, box);
      drafts.prepend(item);
    }

    // Auto-fill WhatsApp from mobile number
    document.getElementById('mobile').addEventListener('input', function() {
      const whatsappField = document.getElementById('whatsapp');
      if (!whatsappField.value) {
        whatsappField.value = this.value;
      }
    });

    // Auto-fill location from city
    document.getElementById('city').addEventListener('input', function() {
      const locationField = document.getElementById('location');
      if (!locationField.value) {
        locationField.value = this.value;
      }
    });

    // Auto-fill registration year from manufacturing year
    document.getElementById('manufacturing_year').addEventListener('input', function() {
      const regYearField = document.getElementById('registration_year');
      if (!regYearField.value) {
        regYearField.value = this.value;
      }
    });

    // Store prediction data for auto-fill
    let predictionData = {};

    // Estimate button -> call backend price predictor and auto-fill form
    document.getElementById('btnEstimate').addEventListener('click', async () => {
      const payload = {
        make: document.getElementById('make').value,
        model: document.getElementById('model').value,
        year: Number(document.getElementById('manufacturing_year').value || 0),
        km: Number(document.getElementById('km').value || 0),
        fuel: document.getElementById('fuel').value,
        trans: document.getElementById('trans').value,
        owners: document.getElementById('owners').value,
        location: document.getElementById('location').value,
      };
      
      // Validate required fields for prediction
      if (!payload.make || !payload.model || !payload.year || !payload.km || !payload.fuel || !payload.trans) {
        alert('Please fill in Brand, Model, Manufacturing Year, KM Driven, Fuel Type, and Transmission Type to get price estimate.');
        return;
      }
      
      const res = await apiPost('/price/predict/', payload);
      if (res && !res.__error && typeof res.estimate === 'number') {
        const currency = res.currency || 'INR';
        const fmt = (n)=> (currency === 'INR' ? `₹${Number(n).toLocaleString('en-IN')}` : `${currency} ${Number(n).toLocaleString()}`);
        const low = (res.low!=null? fmt(res.low): '');
        const high = (res.high!=null? fmt(res.high): '');
        const estimate = fmt(res.estimate);
        
        // Store prediction data
        predictionData = {
          estimate: res.estimate,
          low: res.low,
          high: res.high,
          ...payload
        };
        
        // Auto-fill the expected price field with the estimate
        document.getElementById('price').value = Math.round(res.estimate);
        
        // Show estimate box
        const box = document.getElementById('estimateBox');
        let html = `<div style="font-weight:800;color:#1e3a8a">Estimated market price: ${estimate}</div>`;
        if (low && high) html += `<div style="margin-top:4px;color:#334155">Range: <strong>${low}</strong> – <strong>${high}</strong></div>`;
        html += `<div style="margin-top:8px;font-size:.9rem;color:#475569">✓ Price has been auto-filled in the form. You can adjust it based on your car's condition.</div>`;
        html += `<div style="margin-top:8px;font-size:.9rem;color:#475569">✓ Vehicle details from prediction have been saved.</div>`;
        box.innerHTML = html;
        box.style.display = 'block';
        box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Highlight the price field briefly
        const priceField = document.getElementById('price');
        priceField.style.background = '#dcfce7';
        priceField.style.transition = 'background 0.3s ease';
        setTimeout(() => {
          priceField.style.background = '#fff';
        }, 2000);
        
      } else {
        const box = document.getElementById('estimateBox');
        box.innerHTML = `<div style="color:#b91c1c"><i class="fas fa-exclamation-triangle"></i> Could not fetch estimate: ${(res && res.message) || 'Unknown error'}</div>`;
        box.style.display = 'block';
      }
    });

    // Enhanced form submission with multiple images support
    form.addEventListener('submit', async (e) => {
      // If images are already uploaded, just submit the form
      if (uploadedImageUrls.length > 0) {
        // Images already uploaded, proceed with form submission
        return;
      }
      
      // Legacy fallback: if user selected files but didn't trigger upload
      const files = photos.files;
      if (!files || files.length === 0) {
        // No image selected; allow normal submit
        return;
      }
      
      e.preventDefault();
      
      try {
        // Upload the first image for backward compatibility
        const fd = new FormData();
        fd.append('file', files[0]);
        const resp = await fetch(`${BASE_API}/upload/`, { method: 'POST', body: fd });
        const json = await resp.json();
        if (!resp.ok || !json || !json.url) {
          throw new Error((json && json.detail) || 'Upload failed');
        }
        document.getElementById('img').value = json.url;
        uploadedImageUrls = [json.url];
      } catch (err) {
        console.warn('Image upload failed:', err);
        // proceed without image
      }
      
      // Submit after setting hidden field
      form.submit();
    });
    
    // After successful form submission, add additional images to the listing
    const originalSubmit = form.submit;
    form.submit = function() {
      // Store image URLs for post-submission processing
      if (uploadedImageUrls.length > 1) {
        sessionStorage.setItem('pendingImages', JSON.stringify(uploadedImageUrls.slice(1)));
      }
      originalSubmit.call(this);
    };

    // Load drafts from localStorage for demo sidebar
    (function(){
      const all = JSON.parse(localStorage.getItem('ap_listings')||'[]');
      all.slice(0,5).forEach(renderDraft);
    })();

    // Auto-fill form from URL parameters or localStorage (from price prediction page)
    (function autoFillFromPrediction() {
      // Check URL parameters first
      const urlParams = new URLSearchParams(window.location.search);
      
      // Check localStorage for prediction data
      const savedPrediction = localStorage.getItem('ap_price_prediction');
      let predictionSource = null;
      
      if (urlParams.has('make') || urlParams.has('model')) {
        // Load from URL parameters
        predictionSource = {
          make: urlParams.get('make'),
          model: urlParams.get('model'),
          year: urlParams.get('year'),
          km: urlParams.get('km'),
          fuel: urlParams.get('fuel'),
          trans: urlParams.get('trans'),
          owners: urlParams.get('owners'),
          location: urlParams.get('location'),
          price: urlParams.get('price'),
          estimate: urlParams.get('estimate')
        };
      } else if (savedPrediction) {
        // Load from localStorage
        try {
          predictionSource = JSON.parse(savedPrediction);
        } catch (e) {
          console.warn('Failed to parse saved prediction:', e);
        }
      }
      
      // Auto-fill form if we have prediction data
      if (predictionSource) {
        if (predictionSource.make) document.getElementById('make').value = predictionSource.make;
        if (predictionSource.model) document.getElementById('model').value = predictionSource.model;
        if (predictionSource.year) {
          document.getElementById('manufacturing_year').value = predictionSource.year;
          document.getElementById('registration_year').value = predictionSource.year;
        }
        if (predictionSource.km) document.getElementById('km').value = predictionSource.km;
        if (predictionSource.fuel) document.getElementById('fuel').value = predictionSource.fuel;
        if (predictionSource.trans) document.getElementById('trans').value = predictionSource.trans;
        if (predictionSource.owners) {
          // Convert owners format (1, 2, 3, 4+) to (1st Owner, 2nd Owner, etc.)
          const ownerMap = {
            '1': '1st Owner',
            '2': '2nd Owner',
            '3': '3rd Owner',
            '4': '4th Owner',
            '4+': '4th Owner',
            '5+': '5+ Owner'
          };
          const ownerValue = ownerMap[predictionSource.owners] || predictionSource.owners;
          document.getElementById('owners').value = ownerValue;
        }
        if (predictionSource.location) {
          document.getElementById('location').value = predictionSource.location;
          document.getElementById('city').value = predictionSource.location;
        }
        if (predictionSource.price || predictionSource.estimate) {
          document.getElementById('price').value = predictionSource.price || predictionSource.estimate;
        }
        
        // Show notification that data was auto-filled
        if (predictionSource.make || predictionSource.model) {
          const notification = document.createElement('div');
          notification.style.cssText = 'position:fixed;top:100px;right:20px;background:#10b981;color:#fff;padding:16px 20px;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.2);z-index:9999;animation:slideIn 0.3s ease';
          notification.innerHTML = '<i class="fas fa-check-circle"></i> Vehicle details auto-filled from price prediction!';
          document.body.appendChild(notification);
          
          setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
          }, 3000);
        }
        
        // Clear localStorage after loading
        localStorage.removeItem('ap_price_prediction');
      }
    })();
    
    // Add CSS animations for notification
    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
      @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
      }
    `;
    document.head.appendChild(style);
