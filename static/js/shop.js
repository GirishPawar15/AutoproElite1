    // Create years in Year From select
const yearFrom = document.getElementById('fYearFrom');
for(let y=new Date().getFullYear(); y>=1990; y--){
  const o=document.createElement('option'); o.value=o.textContent=y; yearFrom.appendChild(o);
}

// Load data: prefer API, fallback to localStorage + seed samples
const API_BASE = '/api';
async function getData(){
  try {
    console.log('Fetching listings from API...');
    const t = new Date().getTime();
    const res = await fetch(`${API_BASE}/listings/?t=${t}`);
    if (!res.ok) throw new Error('bad status');

    const apiData = await res.json();
    console.log('API returned', apiData.length, 'listings');
    // Normalize API fields to UI expectation, including id for cart product_id
    return apiData.map(d=>({
      id: d.id,
      make: d.make, model: d.model, year: Number(d.year)||0, km: Number(d.km)||0,
      fuel: d.fuel||'-', trans: d.trans||'-', price: Number(d.price)||0,
      location: d.location||'-', createdAt: new Date(d.created_at||Date.now()).getTime(),
      img: d.img || 'https://images.unsplash.com/photo-1549924231-f129b911e442?q=80&w=800&auto=format&fit=crop',
      primary_image: d.primary_image || d.img || 'https://images.unsplash.com/photo-1549924231-f129b911e442?q=80&w=800&auto=format&fit=crop',
      all_images: d.all_images || [d.img || 'https://images.unsplash.com/photo-1549924231-f129b911e442?q=80&w=800&auto=format&fit=crop'],
      seller_username: d.seller_username || d.seller || '',
      seller_email: d.seller_email || '',
      seller_phone: d.seller_phone || ''
    }));
  } catch (e) {
    console.log('API failed, using fallback data:', e);
    const user = JSON.parse(localStorage.getItem('ap_listings')||'[]');
    const seed = [
      {id: 100001, make:'Toyota', model:'Corolla', year:2019, km:45000, fuel:'Petrol', trans:'Automatic', price:950000, location:'Delhi', createdAt:Date.now()-86400000*10, img:'https://images.unsplash.com/photo-1549924231-f129b911e442?q=80&w=800&auto=format&fit=crop'},
      {id: 100002, make:'Honda', model:'Civic', year:2018, km:52000, fuel:'Petrol', trans:'Manual', price:875000, location:'Mumbai', createdAt:Date.now()-86400000*20, img:'https://images.unsplash.com/photo-1493238792000-8113da705763?q=80&w=800&auto=format&fit=crop'},
      {id: 100003, make:'Hyundai', model:'i20', year:2021, km:22000, fuel:'Diesel', trans:'Manual', price:720000, location:'Bangalore', createdAt:Date.now()-86400000*5, img:'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?q=80&w=800&auto=format&fit=crop'},
      {id: 100004, make:'Maruti', model:'Swift', year:2017, km:60000, fuel:'Petrol', trans:'AMT', price:520000, location:'Pune', createdAt:Date.now()-86400000*40, img:'https://images.unsplash.com/photo-1503376780353-7e6692767b70?q=80&w=800&auto=format&fit=crop'}
    ];
    const mappedUser = user.map((d, idx)=>(
      {
      ...d,
      id: d.id ?? d.listing_id ?? (200000 + idx),
      km: Number(d.km||0),
      year: Number(d.year||0),
      price: Number(d.price||0),
      img: 'https://images.unsplash.com/photo-1549924231-f129b911e442?q=80&w=800&auto=format&fit=crop',
      seller_username: d.seller_username||'', seller_email: d.seller_email||'', seller_phone: d.seller_phone||''
    }));
    return [...mappedUser, ...seed];
  }
}

// Contact details modal
const modal = document.getElementById('contactModal');
const mClose = document.getElementById('m_close');
function showContact(d){
  document.getElementById('m_name').textContent = `${d.seller_username||'Seller'}`;
  document.getElementById('m_email').textContent = d.seller_email||'autoproelite@gmail.com';
  document.getElementById('m_phone').textContent = d.seller_phone||'9850767273';
  document.getElementById('m_loc').textContent = d.location||'-';
  if(modal){ modal.style.display='flex'; }
}
if(mClose && modal){ mClose.addEventListener('click', ()=> modal.style.display='none'); }
if(modal){ modal.addEventListener('click', (e)=>{ if(e.target===modal) modal.style.display='none'; }); }

// EMI Calculator Modal
const emiModal = document.getElementById('emiModal');
const emiClose = document.getElementById('emi_close');
let currentCarPrice = 0;

function showEMICalculator(price) {
  currentCarPrice = price;
  // Set initial loan amount to 75% of car price
  const loanAmount = Math.round(price * 0.75);
  document.getElementById('loanAmount').value = loanAmount;
  updateEMI();
  if(emiModal){ emiModal.style.display = 'flex'; }
}

if(emiClose && emiModal){ emiClose.addEventListener('click', ()=> emiModal.style.display='none'); }
if(emiModal){ emiModal.addEventListener('click', (e)=>{ if(e.target===emiModal) emiModal.style.display='none'; }); }

// EMI Calculation Function
function calculateEMI(principal, rate, tenure) {
  const monthlyRate = rate / 12 / 100;
  const months = tenure * 12;
  const emi = (principal * monthlyRate * Math.pow(1 + monthlyRate, months)) / (Math.pow(1 + monthlyRate, months) - 1);
  return Math.round(emi);
}

function updateEMI() {
  const loanAmount = parseInt(document.getElementById('loanAmount').value);
  const interestRate = parseFloat(document.getElementById('interestRate').value);
  const duration = parseInt(document.getElementById('duration').value);
  
  // Calculate EMI
  const emi = calculateEMI(loanAmount, interestRate, duration);
  const totalPayable = emi * duration * 12;
  const totalInterest = totalPayable - loanAmount;
  
  // Update display values
  document.getElementById('emiAmount').textContent = emi.toLocaleString('en-IN');
  document.getElementById('emiTenure').textContent = duration * 12;
  document.getElementById('emiRate').textContent = interestRate.toFixed(1);
  document.getElementById('principalAmount').textContent = loanAmount.toLocaleString('en-IN');
  document.getElementById('interestAmount').textContent = totalInterest.toLocaleString('en-IN');
  document.getElementById('totalAmount').textContent = totalPayable.toLocaleString('en-IN');
  
  // Update slider values
  document.getElementById('loanAmountValue').textContent = '₹' + loanAmount.toLocaleString('en-IN');
  document.getElementById('interestRateValue').textContent = interestRate.toFixed(1) + '%';
  document.getElementById('durationValue').textContent = duration + (duration === 1 ? ' Year' : ' Years');
  
  // Update slider tracks
  const loanPercent = ((loanAmount - 50000) / (9000000 - 50000)) * 100;
  const ratePercent = ((interestRate - 5) / (30 - 5)) * 100;
  const durationPercent = ((duration - 1) / (5 - 1)) * 100;
  
  document.getElementById('loanTrack').style.width = loanPercent + '%';
  document.getElementById('rateTrack').style.width = ratePercent + '%';
  document.getElementById('durationTrack').style.width = durationPercent + '%';
  
  // Update pie chart
  const principalPercent = (loanAmount / totalPayable) * 314;
  const interestPercent = (totalInterest / totalPayable) * 314;
  
  document.getElementById('principalArc').setAttribute('stroke-dasharray', `${principalPercent} 314`);
  document.getElementById('principalArc').setAttribute('stroke-dashoffset', '0');
  document.getElementById('interestArc').setAttribute('stroke-dasharray', `${interestPercent} 314`);
  document.getElementById('interestArc').setAttribute('stroke-dashoffset', -principalPercent);
}
    
    // Attach slider event listeners
    document.getElementById('loanAmount').addEventListener('input', updateEMI);
    document.getElementById('interestRate').addEventListener('input', updateEMI);
    document.getElementById('duration').addEventListener('input', updateEMI);

    // Test Drive Booking Modal
    const testDriveModal = document.getElementById('testDriveModal');
    const tdClose = document.getElementById('td_close');
    const tdSubmit = document.getElementById('td_submit');
    const testDriveForm = document.getElementById('testDriveForm');
    let currentTestDriveCar = null;
    
    function showTestDriveBooking(car) {
      currentTestDriveCar = car;
      
      // Populate car details
      const primaryImage = car.all_images && car.all_images.length > 0 ? car.all_images[0] : car.img;
      document.getElementById('td_car_image').src = primaryImage || 'https://images.unsplash.com/photo-1549924231-f129b911e442?q=80&w=800&auto=format&fit=crop';
      document.getElementById('td_car_name').textContent = `${car.make} ${car.model} ${car.year}`;
      document.getElementById('td_car_price').textContent = `₹${Number(car.price).toLocaleString('en-IN')}`;
      document.getElementById('td_car_location').innerHTML = `<i class="fas fa-location-dot"></i> ${car.location || 'Pune'}`;
      
      // Set minimum date to today
      const today = new Date().toISOString().split('T')[0];
      document.getElementById('td_date').setAttribute('min', today);
      
      // Reset form
      testDriveForm.reset();
      document.getElementById('td_success').style.display = 'none';
      document.getElementById('td_error').style.display = 'none';
      
      // Pre-fill user data if logged in
      const user = JSON.parse(localStorage.getItem('ap_user') || '{}');
      if (user.email) {
        document.getElementById('td_email').value = user.email;
      }
      
      testDriveModal.style.display = 'flex';
    }
    
    if(tdClose){ 
      tdClose.addEventListener('click', ()=> {
        testDriveModal.style.display='none';
      }); 
    }
    
    if(testDriveModal){ 
      testDriveModal.addEventListener('click', (e)=>{ 
        if(e.target===testDriveModal) testDriveModal.style.display='none'; 
      }); 
    }
    
    if(tdSubmit){
      tdSubmit.addEventListener('click', async (e)=> {
        e.preventDefault();
        
        // Validate form
        if (!testDriveForm.checkValidity()) {
          testDriveForm.reportValidity();
          return;
        }
        
        // Get form data
        const formData = {
          car_id: currentTestDriveCar.id,
          car_name: `${currentTestDriveCar.make} ${currentTestDriveCar.model} ${currentTestDriveCar.year}`,
          car_price: currentTestDriveCar.price,
          name: document.getElementById('td_name').value,
          phone: document.getElementById('td_phone').value,
          email: document.getElementById('td_email').value,
          city: document.getElementById('td_city').value,
          preferred_date: document.getElementById('td_date').value,
          preferred_time: document.getElementById('td_time').value,
          message: document.getElementById('td_message').value,
          booking_date: new Date().toISOString()
        };
        
        // Show loading state
        tdSubmit.disabled = true;
        tdSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Booking...';
        
        try {
          // Send booking request
          const token = localStorage.getItem('ap_token');
          const headers = {
            'Content-Type': 'application/json'
          };
          
          if (token) {
            headers['Authorization'] = `Token ${token}`;
          }
          
          const response = await fetch('/api/testdrive/book/', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(formData)
          });
          
          if (response.ok) {
            // Show success message
            document.getElementById('td_success').style.display = 'flex';
            document.getElementById('td_error').style.display = 'none';
            testDriveForm.style.display = 'none';
            
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
                  description: `Booked test drive for ${formData.car_name}`
                })
              }).catch(err => console.log('Activity log failed:', err));
            }
            
            // Close modal after 3 seconds
            setTimeout(() => {
              testDriveModal.style.display = 'none';
              testDriveForm.style.display = 'flex';
              testDriveForm.reset();
            }, 3000);
          } else {
            throw new Error('Booking failed');
          }
        } catch (error) {
          console.error('Test drive booking error:', error);
          document.getElementById('td_error_message').textContent = 'Failed to book test drive. Please try again or contact us directly.';
          document.getElementById('td_error').style.display = 'flex';
          document.getElementById('td_success').style.display = 'none';
        } finally {
          tdSubmit.disabled = false;
          tdSubmit.innerHTML = '<i class="fas fa-calendar-check"></i> Confirm Booking';
        }
      });
    }

    // Compare Feature
    let compareList = [];
    const MAX_COMPARE = 3;
    const compareBar = document.getElementById('compareBar');
    const compareItems = document.getElementById('compareItems');
    const compareCount = document.getElementById('compareCount');
    const compareBtn = document.getElementById('compareBtn');
    const clearCompareBtn = document.getElementById('clearCompareBtn');
    const compareModal = document.getElementById('compareModal');
    const compareClose = document.getElementById('compare_close');
    
    function addToCompare(car) {
      if (compareList.find(c => c.id === car.id)) {
        removeFromCompare(car.id);
        return;
      }
      
      if (compareList.length >= MAX_COMPARE) {
        alert(`You can compare maximum ${MAX_COMPARE} cars at a time`);
        return;
      }
      
      compareList.push(car);
      updateCompareBar();
    }
    
    function removeFromCompare(carId) {
      compareList = compareList.filter(c => c.id !== carId);
      updateCompareBar();
      
      // Update checkbox in card
      const checkbox = document.querySelector(`input[data-compare-id="${carId}"]`);
      if (checkbox) checkbox.checked = false;
    }
    
    function updateCompareBar() {
      compareCount.textContent = compareList.length;
      compareBtn.disabled = compareList.length < 2;
      
      if (compareList.length > 0) {
        compareBar.classList.add('active');
      } else {
        compareBar.classList.remove('active');
      }
      
      compareItems.innerHTML = compareList.map(car => `
        <div class="compare-item">
          <img src="${car.primary_image || car.img}" alt="${car.make} ${car.model}">
          <div class="compare-item-info">
            <div class="compare-item-name">${car.make} ${car.model}</div>
            <div class="compare-item-price">₹${Number(car.price).toLocaleString('en-IN')}</div>
          </div>
          <button class="compare-item-remove" onclick="removeFromCompare(${car.id})">
            <i class="fas fa-times"></i>
          </button>
        </div>
      `).join('');
    }
    
    function showCompareModal() {
      if (compareList.length < 2) {
        alert('Please select at least 2 cars to compare');
        return;
      }
      
      const grid = document.getElementById('compareGrid');
      
      // Build comparison table
      let html = '';
      
      // Header row with car cards
      html += '<div class="compare-label"></div>'; // Empty corner cell
      compareList.forEach(car => {
        html += `
          <div class="compare-car-card">
            <button class="compare-remove-btn" onclick="removeFromCompare(${car.id})">
              <i class="fas fa-times"></i>
            </button>
            <img src="${car.primary_image || car.img}" alt="${car.make} ${car.model}">
            <div class="compare-car-name">${car.make} ${car.model}</div>
            <div class="compare-car-price">₹${Number(car.price).toLocaleString('en-IN')}</div>
            <button class="compare-book-btn" data-car-id="${car.id}">BOOK A TEST DRIVE</button>
          </div>
        `;
      });
      
      // Add car button if less than max
      if (compareList.length < MAX_COMPARE) {
        html += `
          <div class="compare-add-card" onclick="compareModal.style.display='none'">
            <i class="fas fa-plus-circle"></i>
            <div style="font-weight:600;color:var(--muted)">Add Car</div>
          </div>
        `;
      }
      
      // Overview Section
      html += '<div class="compare-section-header">Overview</div>';
      
      const specs = [
        { label: 'Price', key: 'price', format: (v) => '₹' + Number(v).toLocaleString('en-IN') },
        { label: 'Year', key: 'year' },
        { label: 'Kilometers Driven', key: 'km', format: (v) => Number(v).toLocaleString() + ' km' },
        { label: 'Fuel Type', key: 'fuel' },
        { label: 'Transmission', key: 'trans' },
        { label: 'Location', key: 'location' },
        { label: 'No. of Owner(s)', key: 'owners', default: '1st Owner' },
        { label: 'Color', key: 'color', default: 'Not specified' },
      ];
      
      specs.forEach(spec => {
        html += `<div class="compare-label">${spec.label}</div>`;
        compareList.forEach(car => {
          let value = car[spec.key] || spec.default || '-';
          if (spec.format) value = spec.format(value);
          html += `<div class="compare-value">${value}</div>`;
        });
        if (compareList.length < MAX_COMPARE) {
          html += '<div class="compare-value">-</div>';
        }
      });
      
      // Features Section
      html += '<div class="compare-section-header">Features & Ratings</div>';
      
      html += '<div class="compare-label">Overall Rating</div>';
      compareList.forEach(() => {
        html += '<div class="compare-value"><div class="rating">' + 
          Array(5).fill(0).map((_, i) => `<i class="fas fa-star" style="color:${i < 4 ? '#f59e0b' : '#e5e7eb'}"></i>`).join('') +
          '</div></div>';
      });
      if (compareList.length < MAX_COMPARE) html += '<div class="compare-value">-</div>';
      
      html += '<div class="compare-label">Warranty</div>';
      compareList.forEach(() => {
        html += '<div class="compare-value">1 Year Warranty</div>';
      });
      if (compareList.length < MAX_COMPARE) html += '<div class="compare-value">-</div>';
      
      html += '<div class="compare-label">Certified</div>';
      compareList.forEach(() => {
        html += '<div class="compare-value"><span class="badge certified"><i class="fas fa-certificate"></i> Certified</span></div>';
      });
      if (compareList.length < MAX_COMPARE) html += '<div class="compare-value">-</div>';
      
      grid.innerHTML = html;
      
      // Add event listeners for test drive buttons in compare modal
      setTimeout(() => {
        document.querySelectorAll('.compare-book-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            const carId = parseInt(e.target.dataset.carId);
            const car = compareList.find(c => c.id === carId);
            if (car) {
              compareModal.style.display = 'none';
              showTestDriveBooking(car);
            }
          });
        });
      }, 0);
      
      compareModal.style.display = 'flex';
    }
    
    if (compareBtn) compareBtn.addEventListener('click', showCompareModal);
    if (clearCompareBtn) clearCompareBtn.addEventListener('click', () => {
      compareList = [];
      updateCompareBar();
      // Uncheck all compare checkboxes
      document.querySelectorAll('input[data-compare-id]').forEach(cb => cb.checked = false);
    });
    if (compareClose) compareClose.addEventListener('click', () => compareModal.style.display = 'none');
    if (compareModal) compareModal.addEventListener('click', (e) => {
      if (e.target === compareModal) compareModal.style.display = 'none';
    });
    
    // Make removeFromCompare global
    window.removeFromCompare = removeFromCompare;

    const state = { q:'', f:{}, sort:'-createdAt', data:[] };

    function apply(){
      const q = state.q.trim().toLowerCase();
      const {make, model, min, max, yearFrom, fuel} = state.f;
      let list = [...state.data];

      if(q){
        list = list.filter(d=>`${d.make} ${d.model} ${d.location}`.toLowerCase().includes(q));
      }
      if(make){ list = list.filter(d=>d.make.toLowerCase().includes(make)); }
      if(model){ list = list.filter(d=>d.model.toLowerCase().includes(model)); }
      if(min!=null && min!==''){ list = list.filter(d=>Number(d.price)>=Number(min)); }
      if(max!=null && max!==''){ list = list.filter(d=>Number(d.price)<=Number(max)); }
      if(yearFrom){ list = list.filter(d=>Number(d.year)>=Number(yearFrom)); }
      if(fuel){ list = list.filter(d=>String(d.fuel).toLowerCase()===fuel.toLowerCase()); }

      switch(state.sort){
        case 'price': list.sort((a,b)=>a.price-b.price); break;
        case '-price': list.sort((a,b)=>b.price-a.price); break;
        case 'year': list.sort((a,b)=>a.year-b.year); break;
        case '-year': list.sort((a,b)=>b.year-a.year); break;
        default: list.sort((a,b)=>(b.createdAt||0)-(a.createdAt||0));
      }

      render(list);
    }

    function render(list){
      const cards = document.getElementById('cards');
      const empty = document.getElementById('empty');
      const count = document.getElementById('count');
      cards.innerHTML='';
      count.textContent = list.length+ ' results';
      empty.style.display = list.length? 'none':'block';
      list.forEach(d=>{
        const el = document.createElement('div');
        el.className='card';
        
        // Get all images for this listing
        const images = d.all_images && d.all_images.length > 0 ? d.all_images : [d.primary_image || d.img];
        const hasMultipleImages = images.length > 1;
        
        // Calculate EMI (approximate)
        const emiAmount = Math.round((d.price * 0.02)); // Rough 2% monthly EMI
        
        // Generate rating stars
        const rating = 4; // Default rating, can be dynamic
        const stars = Array(5).fill(0).map((_, i) => 
          `<i class="fas fa-star" style="color:${i < rating ? '#f59e0b' : '#e5e7eb'}"></i>`
        ).join('');
        
        // Create image slider HTML
        let sliderHTML = '';
        if (hasMultipleImages) {
          sliderHTML = `
            <div class="image-slider">
              <div class="slider-track">
                ${images.map(img => `<div class="slider-image" style="background-image:url('${img}')"></div>`).join('')}
              </div>
              <button class="slider-nav prev" data-role="slider-prev"><i class="fas fa-chevron-left"></i></button>
              <button class="slider-nav next" data-role="slider-next"><i class="fas fa-chevron-right"></i></button>
              <div class="slider-dots">
                ${images.map((_, i) => `<button class="slider-dot ${i === 0 ? 'active' : ''}" data-index="${i}"></button>`).join('')}
              </div>
              <div class="image-count"><i class="fas fa-images"></i> ${images.length}</div>
            </div>
          `;
        } else {
          sliderHTML = `<div style="width:100%;height:100%;background-image:url('${images[0]}');background-size:cover;background-position:center"></div>`;
        }
        
        el.innerHTML = `
          <div class="thumb">
            ${sliderHTML}
            <div style="position:absolute;top:12px;right:12px;display:flex;gap:8px;z-index:20">
              <button style="background:rgba(255,255,255,0.9);border:none;width:36px;height:36px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.1)">
                <i class="fas fa-heart" style="color:#ef4444"></i>
              </button>
              <button style="background:rgba(255,255,255,0.9);border:none;width:36px;height:36px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.1)">
                <i class="fas fa-share-alt" style="color:#64748b"></i>
              </button>
            </div>
          </div>
          <div class="box">
            <div class="badge-row">
              <span class="badge certified"><i class="fas fa-certificate"></i> Certified</span>
              <span class="badge warranty"><i class="fas fa-shield-alt"></i> 1 Year Warranty</span>
            </div>
            
            <h3 class="title">${d.make} ${d.model}</h3>
            
            <div class="location-text">
              <i class="fas fa-map-marker-alt"></i>
              ${d.location || 'Pune'}
            </div>
            
            <div class="meta">
              <span class="meta-item"><i class="fas fa-calendar"></i> ${d.year}</span>
              <span class="meta-item"><i class="fas fa-gas-pump"></i> ${d.fuel || 'Petrol'}</span>
              <span class="meta-item"><i class="fas fa-tachometer-alt"></i> ${Number(d.km).toLocaleString()} km</span>
            </div>
            
            <div class="rating">
              ${stars}
            </div>
            
            <div class="price-section">
              <div>
                <div class="price">₹${Number(d.price).toLocaleString('en-IN')}</div>
              </div>
              <div class="emi-info">
                <button class="emi-btn">CALCULATE EMI</button>
                <div style="margin-top:4px">EMI Starts ₹${emiAmount.toLocaleString('en-IN')}*</div>
              </div>
            </div>
            
            <div class="finance-option">
              <input type="checkbox" id="compare-${d.id}" data-compare-id="${d.id}">
              <label for="compare-${d.id}" style="cursor:pointer">Add to Compare</label>
            </div>
            
            <div class="icon-actions">
              <a href="/car/${d.id}/" class="icon-action">
                <i class="fas fa-car"></i>
                <span>About Car</span>
              </a>
              <div class="icon-action" data-role="compare">
                <i class="fas fa-exchange-alt"></i>
                <span>Compare Cars</span>
              </div>
              <div class="icon-action" data-role="finance">
                <i class="fas fa-hand-holding-usd"></i>
                <span>Smart Finance</span>
              </div>
            </div>
            
            <div class="action-buttons">
              <button class="btn-action btn-contact" data-role="contact">
                <i class="fas fa-phone"></i>
                CONTACT DEALER
              </button>
              <button class="btn-action btn-book" data-role="view-details">
                <i class="fas fa-calendar-check"></i>
                BOOK A TEST DRIVE
              </button>
            </div>
          </div>`;
        
        cards.appendChild(el);
        
        // Setup slider functionality if multiple images
        if (hasMultipleImages) {
          let currentIndex = 0;
          const track = el.querySelector('.slider-track');
          const dots = el.querySelectorAll('.slider-dot');
          const prevBtn = el.querySelector('[data-role="slider-prev"]');
          const nextBtn = el.querySelector('[data-role="slider-next"]');
          
          function updateSlider(index) {
            currentIndex = index;
            track.style.transform = `translateX(-${currentIndex * 100}%)`;
            dots.forEach((dot, i) => {
              dot.classList.toggle('active', i === currentIndex);
            });
          }
          
          prevBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const newIndex = currentIndex > 0 ? currentIndex - 1 : images.length - 1;
            updateSlider(newIndex);
          });
          
          nextBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const newIndex = currentIndex < images.length - 1 ? currentIndex + 1 : 0;
            updateSlider(newIndex);
          });
          
          dots.forEach((dot, index) => {
            dot.addEventListener('click', (e) => {
              e.stopPropagation();
              updateSlider(index);
            });
          });
          
          // Touch/swipe support for mobile
          let touchStartX = 0;
          let touchEndX = 0;
          const slider = el.querySelector('.image-slider');
          
          slider.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
          });
          
          slider.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
          });
          
          function handleSwipe() {
            if (touchEndX < touchStartX - 50) {
              const newIndex = currentIndex < images.length - 1 ? currentIndex + 1 : 0;
              updateSlider(newIndex);
            }
            if (touchEndX > touchStartX + 50) {
              const newIndex = currentIndex > 0 ? currentIndex - 1 : images.length - 1;
              updateSlider(newIndex);
            }
          }
        }
        
        // Attach other handlers
        const cbtn = el.querySelector('[data-role="contact"]');
        const vbtn = el.querySelector('[data-role="view-details"]');
        const aboutLink = el.querySelector('a.icon-action[href^="/car/"]');
        const compareBtn = el.querySelector('[data-role="compare"]');
        const financeBtn = el.querySelector('[data-role="finance"]');
        const emiBtn = el.querySelector('.emi-btn');
        const compareCheckbox = el.querySelector('input[data-compare-id]');
        
        if(cbtn){ cbtn.addEventListener('click', ()=> showContact(d)); }
        if(vbtn){ vbtn.addEventListener('click', ()=> showTestDriveBooking(d)); }
        if(aboutLink){ aboutLink.addEventListener('click', ()=> {
          try {
            localStorage.setItem(`ap_listing_${d.id}`, JSON.stringify(d));
          } catch (e) {
            // ignore storage failures
          }
        }); }
        if(compareBtn){ compareBtn.addEventListener('click', ()=> addToCompare(d)); }
        if(financeBtn){ financeBtn.addEventListener('click', ()=> window.open('https://www.hdfc.bank.in/pre-owned-car-loan?icid=website_organic_nav_loans:link:preownedcarloan', '_blank')); }
        if(emiBtn){ emiBtn.addEventListener('click', (e)=> {
          e.stopPropagation();
          showEMICalculator(d.price);
        }); }
        if(compareCheckbox){ compareCheckbox.addEventListener('change', (e)=> {
          if(e.target.checked) {
            addToCompare(d);
          } else {
            removeFromCompare(d.id);
          }
        }); }
      });
    }

    // Wire controls
    document.getElementById('q').addEventListener('input', e=>{ state.q=e.target.value; apply(); });
    document.getElementById('sort').addEventListener('change', e=>{ state.sort=e.target.value; apply(); });
    document.getElementById('btnApply').addEventListener('click', ()=>{
      state.f = {
        make: document.getElementById('fMake').value.trim().toLowerCase(),
        model: document.getElementById('fModel').value.trim().toLowerCase(),
        min: document.getElementById('fMin').value,
        max: document.getElementById('fMax').value,
        yearFrom: document.getElementById('fYearFrom').value,
        fuel: document.getElementById('fFuel').value
      };
      apply();
    });
    document.getElementById('btnClear').addEventListener('click', ()=>{
      ['fMake','fModel','fMin','fMax','fYearFrom','fFuel'].forEach(id=>document.getElementById(id).value='');
      state.q=''; document.getElementById('q').value='';
      state.f={}; state.sort='-createdAt'; document.getElementById('sort').value='-createdAt';
      apply();
    });

    // Add to Cart with login requirement
    async function addToCart(item){
      const token = localStorage.getItem('ap_token');
      const user = localStorage.getItem('ap_user');
      if(!token || !user){
        // Require login
        window.location.href = '/login/?next='+encodeURIComponent('/account/');
        return;
      }
      // Try API first, then fallback to localStorage cart
      const payload = { product_id: String(item.id || `${item.make}-${item.model}-${item.year}`), name: `${item.make} ${item.model}`.trim(), price: Number(item.price)||0, quantity: 1, image_url: item.img, meta: { year:item.year, km:item.km, fuel:item.fuel, trans:item.trans, location:item.location } };
      try {
        const res = await fetch('/api/cart/add/', { method:'POST', headers:{ 'Content-Type':'application/json', 'Authorization': `Token ${token}` }, body: JSON.stringify(payload) });
        if(!res.ok) throw new Error('API add failed');
        // Optionally show toast
        btnToast('Added to cart');
        setTimeout(()=>location.href='/account/', 350);
      } catch(e){
        // Local cart
        const cart = JSON.parse(localStorage.getItem('ap_cart')||'{"items":[]}');
        const idx = cart.items.findIndex(x=>x.name===payload.name);
        if(idx>=0){ cart.items[idx].quantity += 1; }
        else { cart.items.push(payload); }
        localStorage.setItem('ap_cart', JSON.stringify(cart));
        btnToast('Added to cart');
        setTimeout(()=>location.href='/account/', 350);
      }
    }

    function btnToast(msg){
      let t = document.getElementById('ap_toast');
      if(!t){ t = document.createElement('div'); t.id='ap_toast'; t.style.cssText='position:fixed;bottom:20px;right:20px;background:#111827;color:#fff;padding:10px 14px;border-radius:10px;box-shadow:0 10px 20px rgba(0,0,0,.2);z-index:2000;opacity:0;transform:translateY(8px);transition:all .25s'; document.body.appendChild(t); }
      t.textContent = msg; requestAnimationFrame(()=>{ t.style.opacity='1'; t.style.transform='translateY(0)'; });
      setTimeout(()=>{ t.style.opacity='0'; t.style.transform='translateY(8px)'; }, 1400);
    }

    // Initial load
    (async function load(){
      try { state.data = await getData(); }
      catch { state.data = []; }
      apply();
    })();