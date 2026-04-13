 const API_BASE = '/api';
    let cartData = null;
    let selectedPaymentMethod = 'cod';
    
    // Load cart data and populate order summary
    async function loadCart() {
      const token = localStorage.getItem('ap_token');
      if (!token) {
        alert('Please login to continue');
        window.location.href = '/login/';
        return;
      }
      
      try {
        const response = await fetch(`${API_BASE}/cart/`, {
          headers: { 'Authorization': `Token ${token}` }
        });
        
        if (!response.ok) {
          throw new Error('Failed to load cart');
        }
        
        const data = await response.json();
        console.log('Cart data from API:', data);
        
        // Ensure cartData has the correct structure
        cartData = {
          items: data.items || [],
          total_items: data.total_items || 0,
          total_price: data.total_price || 0
        };
        
        renderOrderSummary();
        
      } catch (error) {
        console.error('Error loading cart:', error);
        // Fallback to localStorage cart
        const localCart = JSON.parse(localStorage.getItem('ap_cart') || '{"items":[]}');
        cartData = {
          items: localCart.items || [],
          total_items: localCart.items ? localCart.items.length : 0,
          total_price: 0
        };
        renderOrderSummary();
      }
    }
    
    function renderOrderSummary() {
      const orderItems = document.getElementById('orderItems');
      const subtotalEl = document.getElementById('subtotal');
      const totalEl = document.getElementById('total');
      
      if (!cartData || !cartData.items || cartData.items.length === 0) {
        orderItems.innerHTML = '<p style="color:var(--gray); text-align:center; padding:20px">Your cart is empty</p>';
        subtotalEl.textContent = '₹0';
        totalEl.textContent = '₹50';
        return;
      }
      
      // Render cart items
      orderItems.innerHTML = cartData.items.map(item => `
        <div class="summary-item" style="align-items:flex-start; padding:12px 0">
          ${item.image_url ? `<img src="${item.image_url}" alt="${item.name}" class="item-image">` : ''}
          <div class="item-details">
            <p class="item-name">${item.name}</p>
            <p class="item-meta">Qty: ${item.quantity} × ₹${Number(item.price).toLocaleString('en-IN')}</p>
          </div>
          <div style="font-weight:600">₹${(Number(item.price) * item.quantity).toLocaleString('en-IN')}</div>
        </div>
      `).join('');
      
      // Calculate totals
      const subtotal = cartData.items.reduce((sum, item) => sum + (Number(item.price) * item.quantity), 0);
      const delivery = 50; // Fixed delivery charge
      const total = subtotal + delivery;
      
      subtotalEl.textContent = `₹${subtotal.toLocaleString('en-IN')}`;
      totalEl.textContent = `₹${total.toLocaleString('en-IN')}`;
    }
    
    // Payment method selection
    document.addEventListener('DOMContentLoaded', function() {
      const paymentOptions = document.querySelectorAll('.payment-option');
      const upiApps = document.getElementById('upiApps');
      
      paymentOptions.forEach(option => {
        option.addEventListener('click', function() {
          if (this.classList.contains('disabled')) return;
          
          // Remove selected class from all options
          paymentOptions.forEach(opt => opt.classList.remove('selected'));
          
          // Add selected class to clicked option
          this.classList.add('selected');
          
          // Get selected payment method
          const radio = this.querySelector('input[type="radio"]');
          if (radio) {
            radio.checked = true;
            selectedPaymentMethod = radio.value;
            
            // Show/hide UPI apps
            if (selectedPaymentMethod === 'upi') {
              upiApps.style.display = 'grid';
            } else {
              upiApps.style.display = 'none';
            }
          }
        });
      });
      
      // UPI app selection
      document.querySelectorAll('.upi-app').forEach(app => {
        app.addEventListener('click', function(e) {
          e.preventDefault();
          const appName = this.dataset.app;
          processUPIPayment(appName);
        });
      });
      
      // Place order button
      document.getElementById('placeOrderBtn').addEventListener('click', placeOrder);
      
      // Load cart on page load
      loadCart();
    });
    
    async function placeOrder() {
      const form = document.getElementById('addressForm');
      const formData = new FormData(form);
      
      // Validate form
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      
      // Check if cart has items
      if (!cartData || !cartData.items || cartData.items.length === 0) {
        showError('Your cart is empty. Please add items before placing an order.');
        return;
      }
      
      // Show loading
      document.getElementById('placeOrderBtn').style.display = 'none';
      document.getElementById('loading').style.display = 'block';
      document.getElementById('error').style.display = 'none';
      
      try {
        const token = localStorage.getItem('ap_token');
        if (!token) {
          throw new Error('Please login to continue');
        }
        
        // Prepare cart items with correct structure
        const preparedCartItems = cartData.items.map(item => ({
          product_id: item.product_id || item.id || '',
          name: item.name || '',
          price: parseFloat(item.price) || 0,
          quantity: parseInt(item.quantity) || 1,
          image_url: item.image_url || ''
        }));
        
        const orderData = {
          payment_method: selectedPaymentMethod,
          delivery_address: {
            full_name: formData.get('fullName'),
            phone: formData.get('phone'),
            address: formData.get('address'),
            city: formData.get('city'),
            pincode: formData.get('pincode')
          },
          cart_items: preparedCartItems
        };
        
        console.log('Sending order data:', orderData);
        console.log('Using token:', token);
        
        const response = await fetch(`${API_BASE}/orders/create/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`
          },
          body: JSON.stringify(orderData)
        });
        
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        
        const responseData = await response.json();
        console.log('Server response:', responseData);
        
        if (!response.ok) {
          throw new Error(responseData.detail || responseData.message || 'Failed to create order');
        }
        
        const order = responseData;
        
        // Handle different payment methods
        if (selectedPaymentMethod === 'cod') {
          showSuccess(order);
        } else if (selectedPaymentMethod === 'upi') {
          // UPI payment will be handled by app selection
          showSuccess(order);
        }
        
      } catch (error) {
        console.error('Error placing order:', error);
        showError(error.message || 'Failed to place order. Please try again.');
      }
    }
    
    function processUPIPayment(appName) {
      if (!cartData || !cartData.items) return;
      
      const total = cartData.items.reduce((sum, item) => sum + (Number(item.price) * item.quantity), 0) + 50;
      const orderId = 'AP' + Date.now();
      
      // Generate UPI deep link
      const upiId = 'autoproelite@paytm'; // Replace with your UPI ID
      const merchantName = 'AutoPro Elite';
      const note = `Order ${orderId} - Spare Parts`;
      
      let upiLink = `upi://pay?pa=${upiId}&pn=${merchantName}&am=${total}&cu=INR&tn=${encodeURIComponent(note)}`;
      
      // App-specific deep links
      switch(appName) {
        case 'phonepe':
          upiLink = `phonepe://pay?pa=${upiId}&pn=${merchantName}&am=${total}&cu=INR&tn=${encodeURIComponent(note)}`;
          break;
        case 'gpay':
          upiLink = `tez://upi/pay?pa=${upiId}&pn=${merchantName}&am=${total}&cu=INR&tn=${encodeURIComponent(note)}`;
          break;
        case 'paytm':
          upiLink = `paytmmp://pay?pa=${upiId}&pn=${merchantName}&am=${total}&cu=INR&tn=${encodeURIComponent(note)}`;
          break;
      }
      
      // Open UPI app
      window.location.href = upiLink;
      
      // Show payment pending message
      setTimeout(() => {
        if (confirm('Have you completed the payment? Click OK if payment is successful.')) {
          placeOrder();
        }
      }, 3000);
    }
    
    function showSuccess(order) {
      document.getElementById('loading').style.display = 'none';
      document.getElementById('success').style.display = 'block';
      
      setTimeout(() => {
        window.location.href = `/orders/?order=${order.id}`;
      }, 2000);
    }
    
    function showError(message) {
      document.getElementById('loading').style.display = 'none';
      document.getElementById('placeOrderBtn').style.display = 'block';
      document.getElementById('errorMessage').textContent = message;
      document.getElementById('error').style.display = 'block';
    }
