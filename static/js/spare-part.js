    // State
    let PARTS = [];
    const grid=document.getElementById('grid');
    const search=document.getElementById('search');
    const category=document.getElementById('category');
    const compat=document.getElementById('compat');
    const count=document.getElementById('count');

    function render(items){
      grid.innerHTML=items.map(p=>`<div class="card" data-id="${p.product_id}" data-category="${p.category}" data-compat="${p.compat}">
        <img src="${p.img}" alt="${p.name}">
        <div class="card-body">
          <h3>${p.name}</h3>
          <div class="topbar">
            <span class="price">₹${Number(p.price).toLocaleString('en-IN')}</span>
            <div style="display:flex; gap:6px">
              <button class="btn" onclick="buyNow('${p.product_id}', '${p.name.replace(/'/g, "&#39;")}', ${p.price}, '${p.img}')" style="background:var(--accent); font-size:0.85rem; padding:8px 10px">
                <i class="fas fa-bolt"></i> Buy Now
              </button>
              <button class="btn" onclick="addToCart('${p.product_id}', '${p.name.replace(/'/g, "&#39;")}', ${p.price}, '${p.img}')" style="font-size:0.85rem; padding:8px 10px">
                <i class="fas fa-cart-plus"></i>
              </button>
            </div>
          </div>
          <div class="tag">${p.brand} • ${p.category} • ${p.compat}</div>
        </div>
      </div>`).join('');
      count.textContent=`${items.length} item${items.length!==1?'s':''}`;
    }

    function applyFilters(){
      const q=search.value.trim().toLowerCase();
      const c=category.value;
      const comp=compat.value;
      const filtered=PARTS.filter(p=>
        (q===''||p.name.toLowerCase().includes(q)||p.brand.toLowerCase().includes(q))&&
        (c==='all'||p.category===c)|| (c==='All Categories')
      ).filter(p => (comp==='all'||p.compat===comp)|| (comp==='Compatibility'));
      render(filtered);
    }

    search.addEventListener('input',applyFilters);
    category.addEventListener('change',applyFilters);
    compat.addEventListener('change',applyFilters);

    async function addToCart(id, name, price, img){
      const token = localStorage.getItem('ap_token') || localStorage.getItem('authToken');
      if(!token){
        // Try to open login modal first, fallback to page redirect
        const modal = document.getElementById('loginModal');
        if (modal) {
          modal.classList.add('active');
          document.body.classList.add('modal-open');
        } else {
          const go = confirm('Please login to add items to your cart. Go to login page?');
          if(go) location.href = '/login/';
        }
        return;
      }
      try{
        const res = await fetch('/api/cart/add/',{
          method:'POST',
          headers:{'Content-Type':'application/json', 'Authorization': `Token ${token}`},
          body: JSON.stringify({
            product_id: String(id), // sku preferred
            name,
            price,
            quantity: 1,
            image_url: img
          })
        });
        const data = await res.json();
        if(!res.ok){ throw new Error(data.detail || 'Failed to add to cart'); }
        
        // Show success message with checkout option
        const goToCheckout = confirm(`Added "${name}" to cart! Go to checkout now?`);
        if(goToCheckout) {
          window.location.href = '/checkout/';
        }
      }catch(err){
        alert(err.message || 'Error adding to cart');
      }
    }

    async function buyNow(id, name, price, img) {
      const token = localStorage.getItem('ap_token') || localStorage.getItem('authToken');
      if(!token){
        // Try to open login modal first, fallback to page redirect
        const modal = document.getElementById('loginModal');
        if (modal) {
          modal.classList.add('active');
          document.body.classList.add('modal-open');
        } else {
          const go = confirm('Please login to continue. Go to login page?');
          if(go) location.href = '/login/';
        }
        return;
      }
      
      try {
        // Add to cart first
        const res = await fetch('/api/cart/add/',{
          method:'POST',
          headers:{'Content-Type':'application/json', 'Authorization': `Token ${token}`},
          body: JSON.stringify({
            product_id: String(id),
            name,
            price,
            quantity: 1,
            image_url: img
          })
        });
        
        if(!res.ok) throw new Error('Failed to add to cart');
        
        // Redirect to checkout immediately
        window.location.href = '/checkout/';
        
      } catch(err) {
        alert(err.message || 'Error processing purchase');
      }
    }

    // Load from backend API with graceful fallback
    async function loadParts(){
      console.log('🔄 Loading spare parts from API...');
      try{
        const t = new Date().getTime();
        const res = await fetch(`/api/spareparts/?active=1&t=${t}`);
        console.log('📡 API Response Status:', res.status, res.statusText);
        
        if(!res.ok) {
          console.error('❌ API response not OK:', res.status, res.statusText);
          throw new Error('Bad response');
        }
        
        const data = await res.json();
        console.log('📦 Loaded spare parts from API:', data);
        
        if(!Array.isArray(data)) {
          console.error('❌ API did not return an array:', data);
          throw new Error('Bad response format');
        }
        
        if(data.length === 0) {
          console.warn('⚠️ No spare parts found in database');
          grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding:40px; color:#64748b;"><i class="fas fa-box-open" style="font-size:3rem; margin-bottom:20px; opacity:0.5;"></i><h3>No Spare Parts Available</h3><p>Spare parts inventory is empty. Please add items through the admin panel.</p><p style="margin-top:20px;"><a href="/admin/" class="btn" style="background:var(--primary); color:white; padding:12px 24px; border-radius:8px; text-decoration:none;">Go to Admin Panel</a></p></div>';
          count.textContent = '0 items';
          return;
        }
        
        PARTS = data.map(d=>({
          product_id: d.sku || String(d.id),
          id: d.id,
          name: d.name,
          brand: d.compatible_make || 'OEM',
          category: d.category || 'Misc',
          compat: d.compatible_model || 'Universal',
          price: Number(d.price || 0),
          img: d.image_url || 'https://images.unsplash.com/photo-1542362567-b07e54358753?q=80&w=1200&auto=format&fit=crop'
        }));
        console.log('✅ Successfully loaded', PARTS.length, 'spare parts');
        render(PARTS);
      }catch(e){
        console.error('❌ Error loading spare parts:', e);
        // Show error message with helpful info
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:40px; color:#ef4444;">
          <i class="fas fa-exclamation-triangle" style="font-size:3rem; margin-bottom:20px;"></i>
          <h3>Unable to Load Spare Parts</h3>
          <p>There was an error loading the spare parts catalog.</p>
          <p style="margin-top:20px; color:#64748b;">Error: ${e.message}</p>
          <p style="margin-top:10px; color:#64748b;">Please check:</p>
          <ul style="list-style:none; padding:0; margin-top:10px; color:#64748b;">
            <li>✓ Django server is running</li>
            <li>✓ Database has spare parts (run: python manage.py add_sample_spareparts)</li>
            <li>✓ API endpoint /api/spareparts/ is accessible</li>
          </ul>
          <p style="margin-top:20px;"><a href="/admin/" class="btn" style="background:var(--primary); color:white; padding:12px 24px; border-radius:8px; text-decoration:none;">Go to Admin Panel</a></p>
        </div>`;
        count.textContent = '0 items';
      }
    }

    loadParts();
