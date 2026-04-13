// Migrate legacy auth keys to new ones so account page doesn't force-login
    (function migrateAuthKeys(){
      try{
        const oldT = localStorage.getItem('authToken');
        const oldU = localStorage.getItem('user');
        if(oldT && !localStorage.getItem('ap_token')) localStorage.setItem('ap_token', oldT);
        if(oldU && !localStorage.getItem('ap_user')) localStorage.setItem('ap_user', oldU);
      }catch(e){}
    })();

    // Populate account details from localStorage/API
    function renderCart(cart){
      const list = document.getElementById('cartItems');
      const empty = document.getElementById('cartEmpty');
      const total = document.getElementById('cartTotal');
      const checkoutBtn = document.getElementById('checkoutBtn');
      const clearCartBtn = document.getElementById('clearCartBtn');
      const items = (cart && cart.items) ? cart.items : [];
      
      if(!items.length){
        list.innerHTML = '';
        empty.style.display = 'block';
        total.textContent = 'Total: ₹0 (0 items)';
        checkoutBtn.style.display = 'none';
        clearCartBtn.style.display = 'none';
        return;
      }
      
      empty.style.display = 'none';
      checkoutBtn.style.display = 'inline-flex';
      clearCartBtn.style.display = 'inline-flex';
      
      list.innerHTML = items.map(it => `
        <li class="cart-item">
          ${it.image_url ? `<img src="${it.image_url}" alt="${it.name}">` : ''}
          <div>
            <div class="cart-item-title">${it.name}</div>
            <div class="cart-meta">Qty: ${it.quantity} • ₹${Number(it.price).toLocaleString('en-IN')} each</div>
          </div>
        </li>
      `).join('');
      const totalItems = items.reduce((s, it) => s + it.quantity, 0);
      const totalPrice = items.reduce((s, it) => s + (Number(it.price) * it.quantity), 0);
      total.textContent = `Total: ₹${Number(totalPrice).toLocaleString('en-IN')} (${totalItems} item${totalItems!==1?'s':''})`;
    }

    async function loadAccount(){
      const userRaw = localStorage.getItem('ap_user');
      const token = localStorage.getItem('ap_token');
      const user = userRaw ? JSON.parse(userRaw) : null;
      if (!user || !token){
        // Not logged in
        window.location.href = '/login/';
        return;
      }
      const uname = user.username || user.name || 'user';
      document.getElementById('accUsername').textContent = '@' + uname;
      document.getElementById('accEmail').textContent = user.email || '(no email)';
      document.getElementById('accId').textContent = user.id || '-';
      document.getElementById('accAuth').textContent = token ? 'Authenticated' : 'Not authenticated';
      // Avatar initials
      const initials = String(uname).split(/\s+/).map(s=>s[0]).slice(0,2).join('').toUpperCase();
      const av = document.getElementById('accInitials'); if(av) av.textContent = initials || 'AP';

      // Hide login/signup buttons if logged in
      const loginBtn = document.getElementById('loginBtn');
      const signupBtn = document.getElementById('signupBtn');
      if (loginBtn) loginBtn.style.display = 'none';
      if (signupBtn) signupBtn.style.display = 'none';

      // Fetch cart
      try{
        const res = await fetch('/api/cart/', { headers: { 'Authorization': `Token ${token}` } });
        const data = await res.json();
        if(!res.ok){ throw new Error(data.detail || 'Failed to load cart'); }
        renderCart(data);
      }catch(err){
        console.warn('Cart load failed:', err);
        // Fallback: local cart
        const local = JSON.parse(localStorage.getItem('ap_cart')||'{"items":[]}');
        renderCart(local);
      }
    }

    // Logout
    document.addEventListener('DOMContentLoaded', function(){
      loadAccount();
      const logoutBtn = document.getElementById('logoutBtn');
      const checkoutBtn = document.getElementById('checkoutBtn');
      const clearCartBtn = document.getElementById('clearCartBtn');
      
      logoutBtn.addEventListener('click', function(){
        localStorage.removeItem('ap_token');
        localStorage.removeItem('ap_user');
        // Also clear legacy keys if present
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        window.location.href = '/login/';
      });
      
      checkoutBtn.addEventListener('click', function(){
        window.location.href = '/checkout/';
      });
      
      clearCartBtn.addEventListener('click', async function(){
        if(!confirm('Are you sure you want to clear your cart?')) return;
        
        const token = localStorage.getItem('ap_token');
        try {
          const res = await fetch('/api/cart/clear/', {
            method: 'POST',
            headers: { 'Authorization': `Token ${token}` }
          });
          if(res.ok) {
            renderCart({items: []});
          }
        } catch(err) {
          console.warn('Failed to clear cart via API, clearing locally');
          localStorage.setItem('ap_cart', '{"items":[]}');
          renderCart({items: []});
        }
      });
    });