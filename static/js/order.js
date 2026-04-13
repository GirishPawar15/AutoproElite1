 const BASE_API = (location.origin && location.origin.startsWith('http')) ? (location.origin.replace(/\/$/, '') + '/api') : 'http://127.0.0.1:8000/api';
    function token(){ return localStorage.getItem('ap_token'); }
    async function apiGet(path){
      const r = await fetch(BASE_API + path, { headers: { 'Accept': 'application/json', 'Authorization': 'Token ' + token() }});
      const j = await r.json().catch(()=>({}));
      if(!r.ok) throw new Error(j.detail || ('HTTP ' + r.status));
      return j;
    }
    async function apiPost(path, data){
      const r = await fetch(BASE_API + path, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Token ' + token() }, body: JSON.stringify(data)});
      const j = await r.json().catch(()=>({}));
      if(!r.ok) throw new Error(j.detail || ('HTTP ' + r.status));
      return j;
    }

    function downloadBill(orderId, billNumber) {
      const downloadUrl = BASE_API + '/bills/download/' + orderId + '/';
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = 'Invoice_' + billNumber + '.pdf';
      
      // Add authorization header by fetching and creating blob
      fetch(downloadUrl, {
        headers: {
          'Authorization': 'Token ' + token()
        }
      })
      .then(response => {
        if (!response.ok) throw new Error('Download failed');
        return response.blob();
      })
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Invoice_' + billNumber + '.pdf';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        document.getElementById('msg').textContent = 'Bill downloaded successfully!';
        document.getElementById('msg').style.color = '#28a745';
      })
      .catch(error => {
        document.getElementById('msg').textContent = 'Download failed: ' + error.message;
        document.getElementById('msg').style.color = '#dc3545';
      });
    }

    async function resendEmail(orderId) {
      try {
        await apiPost('/bills/resend/' + orderId + '/', {});
        document.getElementById('msg').textContent = 'Bill email resent successfully!';
        document.getElementById('msg').style.color = '#28a745';
      } catch(e) {
        document.getElementById('msg').textContent = 'Resend failed: ' + e.message;
        document.getElementById('msg').style.color = '#dc3545';
      }
    }

    function renderRows(list){
      const tbody = document.getElementById('ordersBody');
      tbody.innerHTML = '';
      if(!list || list.length === 0){
        tbody.innerHTML = '<tr><td colspan="7" class="muted">No orders yet.</td></tr>';
        return;
      }
      for(const o of list){
        const tr = document.createElement('tr');
        
        // Check if bill exists
        const hasBill = o.bill_number && o.bill_number.trim() !== '';
        const billNumberDisplay = hasBill ? o.bill_number : '<span class="muted">Generating...</span>';
        
        // Build action buttons
        let actionButtons = '';
        
        // Download bill button (if bill exists)
        if (hasBill) {
          actionButtons += `<button class="btn btn-primary btn-sm" data-action="download" data-id="${o.id}" data-bill="${o.bill_number}" title="Download Bill">
            <i class="fas fa-download"></i> Download Bill
          </button> `;
        }
        
        // Resend email button (if bill exists)
        if (hasBill) {
          actionButtons += `<button class="btn btn-outline btn-sm" data-action="resend" data-id="${o.id}" title="Resend Email">
            <i class="fas fa-envelope"></i> Resend
          </button> `;
        }
        
        // Cancel button (if order is pending/paid)
        if (['pending','paid'].includes((o.status||'').toLowerCase())) {
          actionButtons += `<button class="btn btn-danger btn-sm" data-action="cancel" data-id="${o.id}" title="Cancel Order">
            <i class="fas fa-xmark"></i> Cancel
          </button>`;
        }
        
        if (!actionButtons) {
          actionButtons = '<span class="muted">—</span>';
        }
        
        tr.innerHTML = `
          <td>#${o.id}</td>
          <td>${billNumberDisplay}</td>
          <td><span class="badge badge-${(o.status||'').toLowerCase()}">${o.status}</span></td>
          <td>${o.order_type}</td>
          <td><strong>₹${(o.total_amount||0).toLocaleString('en-IN')}</strong></td>
          <td>${(o.created_at||'').replace('T',' ').slice(0,19)}</td>
          <td style="white-space: nowrap;">${actionButtons}</td>`;
        tbody.appendChild(tr);
      }
      
      // Bind action buttons
      tbody.querySelectorAll('button[data-action]').forEach(btn => {
        btn.addEventListener('click', async () => {
          const action = btn.getAttribute('data-action');
          const orderId = btn.getAttribute('data-id');
          const billNumber = btn.getAttribute('data-bill');
          
          if (action === 'download') {
            downloadBill(orderId, billNumber);
          } else if (action === 'resend') {
            await resendEmail(orderId);
          } else if (action === 'cancel') {
            if (confirm('Are you sure you want to cancel order #' + orderId + '?')) {
              try {
                await apiPost('/orders/cancel/', { order_id: orderId });
                document.getElementById('msg').textContent = 'Order #' + orderId + ' cancelled';
                document.getElementById('msg').style.color = '#28a745';
                await load();
              } catch(e) {
                document.getElementById('msg').textContent = 'Cancel failed: ' + e.message;
                document.getElementById('msg').style.color = '#dc3545';
              }
            }
          }
        });
      });
    }

    async function load(){
      try{
        if(!token()){ window.location.href = '/login/'; return; }
        const list = await apiGet('/orders/');
        renderRows(list);
      }catch(e){ 
        document.getElementById('msg').textContent = 'Load failed: ' + e.message;
        document.getElementById('msg').style.color = '#dc3545';
      }
    }
    document.addEventListener('DOMContentLoaded', load);