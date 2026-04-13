// Admin Analytics Dashboard JavaScript

const BASE_API = (location.origin && location.origin.startsWith('http')) 
    ? (location.origin.replace(/\/$/, '') + '/api') 
    : 'http://127.0.0.1:8000/api';

let currentPeriod = 'daily';
let charts = {};

// Get auth token
function getToken() {
    return localStorage.getItem('ap_token') || localStorage.getItem('authToken');
}

// Check if user is admin
function checkAdminAccess() {
    const user = JSON.parse(localStorage.getItem('ap_user') || localStorage.getItem('user') || '{}');
    if (!user.id) {
        window.location.href = '/login/?next=/analytics/';
        return false;
    }
    
    // Hide profit analysis button if not admin
    const profitBtn = document.querySelector('.btn-profit');
    if (profitBtn && !user.is_staff && !user.is_superuser) {
        profitBtn.style.display = 'none';
    }
    
    return true;
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    if (!checkAdminAccess()) return;
    
    initializeCharts();
    loadDashboardData();
    loadRecentOrders();
});

// Change period
function changePeriod(period) {
    currentPeriod = period;
    
    // Update active button
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-period="${period}"]`).classList.add('active');
    
    // Reload data
    loadDashboardData();
}

// Load dashboard data
async function loadDashboardData() {
    try {
        const dates = getDateRange(currentPeriod);
        const token = getToken();
        
        const response = await fetch(
            `${BASE_API}/billing/reports/sales/?start_date=${dates.start}&end_date=${dates.end}`,
            {
                headers: {
                    'Authorization': token ? `Token ${token}` : '',
                    'Accept': 'application/json'
                }
            }
        );
        
        if (response.status === 401 || response.status === 403) {
            alert('Admin access required. Please login as admin.');
            window.location.href = '/login/?next=/analytics/';
            return;
        }
        
        const data = await response.json();
        
        updateStats(data);
        updateCharts(dates);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data. Please try again.');
    }
}

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #ef4444; color: white; padding: 16px 24px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 9999;';
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}

// Get date range based on period
function getDateRange(period) {
    const end = new Date();
    const start = new Date();
    
    if (period === 'daily') {
        start.setDate(end.getDate() - 7);
    } else if (period === 'weekly') {
        start.setDate(end.getDate() - 28);
    } else if (period === 'monthly') {
        start.setMonth(end.getMonth() - 6);
    }
    
    return {
        start: formatDate(start),
        end: formatDate(end)
    };
}

// Format date as YYYY-MM-DD
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// Update stats cards
function updateStats(data) {
    const summary = data.summary || {};
    
    document.getElementById('totalRevenue').textContent = 
        `₹${(summary.total_sales || 0).toLocaleString('en-IN')}`;
    document.getElementById('totalOrders').textContent = 
        summary.total_orders || 0;
    document.getElementById('totalItems').textContent = 
        summary.total_items_sold || 0;
    document.getElementById('avgOrder').textContent = 
        `₹${(summary.average_order_value || 0).toLocaleString('en-IN')}`;
    
    // Update change percentages (mock data for now)
    document.getElementById('revenueChange').textContent = '+12.5%';
    document.getElementById('ordersChange').textContent = '+8.3%';
    document.getElementById('itemsChange').textContent = '+15.7%';
    document.getElementById('avgChange').textContent = '+4.2%';
}

// Initialize all charts
function initializeCharts() {
    // Sales Trend Chart (Line)
    const salesTrendCtx = document.getElementById('salesTrendChart').getContext('2d');
    charts.salesTrend = new Chart(salesTrendCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Sales',
                data: [],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    padding: 12,
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#667eea',
                    borderWidth: 2,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return '₹' + context.parsed.y.toLocaleString('en-IN');
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#f1f5f9'
                    },
                    ticks: {
                        callback: function(value) {
                            return '₹' + value.toLocaleString('en-IN');
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    // Sales Distribution Chart (Pie)
    const salesDistCtx = document.getElementById('salesDistChart').getContext('2d');
    charts.salesDist = new Chart(salesDistCtx, {
        type: 'doughnut',
        data: {
            labels: ['Spare Parts', 'Cars', 'Services'],
            datasets: [{
                data: [60, 30, 10],
                backgroundColor: [
                    '#667eea',
                    '#f093fb',
                    '#4facfe'
                ],
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: {
                            size: 13,
                            weight: '600'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed + '%';
                        }
                    }
                }
            }
        }
    });

    // Top Products Chart (Bar)
    const topProductsCtx = document.getElementById('topProductsChart').getContext('2d');
    charts.topProducts = new Chart(topProductsCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Units Sold',
                data: [],
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: '#667eea',
                borderWidth: 2,
                borderRadius: 8,
                barThickness: 40
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    padding: 12
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: '#f1f5f9'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    // Revenue vs Orders Chart (Mixed)
    const revenueOrdersCtx = document.getElementById('revenueOrdersChart').getContext('2d');
    charts.revenueOrders = new Chart(revenueOrdersCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Revenue',
                    data: [],
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: '#667eea',
                    borderWidth: 2,
                    borderRadius: 8,
                    yAxisID: 'y'
                },
                {
                    label: 'Orders',
                    data: [],
                    type: 'line',
                    borderColor: '#f093fb',
                    backgroundColor: 'rgba(240, 147, 251, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: {
                            size: 13,
                            weight: '600'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    padding: 12
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                    beginAtZero: true,
                    grid: {
                        color: '#f1f5f9'
                    },
                    ticks: {
                        callback: function(value) {
                            return '₹' + value.toLocaleString('en-IN');
                        }
                    }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    beginAtZero: true,
                    grid: {
                        display: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Update charts with real data
async function updateCharts(dates) {
    try {
        // Update Sales Trend
        await updateSalesTrendChart(dates);
        
        // Update Top Products
        await updateTopProductsChart();
        
        // Update Revenue vs Orders
        await updateRevenueOrdersChart(dates);
    } catch (error) {
        console.error('Error updating charts:', error);
    }
}

// Update sales trend chart
async function updateSalesTrendChart(dates) {
    try {
        const token = getToken();
        const labels = [];
        const data = [];
        const start = new Date(dates.start);
        const end = new Date(dates.end);
        
        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
            const dateStr = formatDate(d);
            labels.push(dateStr);
            
            // Fetch daily sales
            const response = await fetch(`${BASE_API}/billing/reports/daily/?date=${dateStr}`, {
                headers: {
                    'Authorization': token ? `Token ${token}` : '',
                    'Accept': 'application/json'
                }
            });
            
            if (response.ok) {
                const dayData = await response.json();
                data.push(dayData.total_sales || 0);
            } else {
                data.push(0);
            }
        }
        
        charts.salesTrend.data.labels = labels.map(d => {
            const date = new Date(d);
            return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
        });
        charts.salesTrend.data.datasets[0].data = data;
        charts.salesTrend.update();
    } catch (error) {
        console.error('Error updating sales trend:', error);
    }
}

// Update top products chart
async function updateTopProductsChart() {
    try {
        const token = getToken();
        const response = await fetch(`${BASE_API}/billing/reports/top-products/?limit=5`, {
            headers: {
                'Authorization': token ? `Token ${token}` : '',
                'Accept': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            const labels = data.products.map(p => p.name);
            const values = data.products.map(p => p.total_quantity);
            
            charts.topProducts.data.labels = labels;
            charts.topProducts.data.datasets[0].data = values;
            charts.topProducts.update();
        }
    } catch (error) {
        console.error('Error updating top products:', error);
    }
}

// Update revenue vs orders chart
async function updateRevenueOrdersChart(dates) {
    try {
        const token = getToken();
        const labels = [];
        const revenueData = [];
        const ordersData = [];
        const start = new Date(dates.start);
        const end = new Date(dates.end);
        
        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
            const dateStr = formatDate(d);
            labels.push(dateStr);
            
            const response = await fetch(`${BASE_API}/billing/reports/daily/?date=${dateStr}`, {
                headers: {
                    'Authorization': token ? `Token ${token}` : '',
                    'Accept': 'application/json'
                }
            });
            
            if (response.ok) {
                const dayData = await response.json();
                revenueData.push(dayData.total_sales || 0);
                ordersData.push(dayData.total_orders || 0);
            } else {
                revenueData.push(0);
                ordersData.push(0);
            }
        }
        
        charts.revenueOrders.data.labels = labels.map(d => {
            const date = new Date(d);
            return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
        });
        charts.revenueOrders.data.datasets[0].data = revenueData;
        charts.revenueOrders.data.datasets[1].data = ordersData;
        charts.revenueOrders.update();
    } catch (error) {
        console.error('Error updating revenue vs orders:', error);
    }
}

// Load recent orders
async function loadRecentOrders() {
    try {
        const token = getToken();
        const response = await fetch(`${BASE_API}/orders/`, {
            headers: {
                'Authorization': token ? `Token ${token}` : '',
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load orders');
        }
        
        const orders = await response.json();
        
        const tbody = document.getElementById('recentOrdersBody');
        tbody.innerHTML = '';
        
        if (!orders || orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">No orders found</td></tr>';
            return;
        }
        
        orders.slice(0, 10).forEach(order => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>#${order.id}</strong></td>
                <td><code>${order.bill_number || 'N/A'}</code></td>
                <td>${order.customer_name || 'Guest'}</td>
                <td>${order.items?.length || 0}</td>
                <td><strong>₹${(order.total_amount || 0).toLocaleString('en-IN')}</strong></td>
                <td>${new Date(order.created_at).toLocaleDateString('en-IN')}</td>
                <td><span class="status-badge ${order.status}">${order.status}</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error loading recent orders:', error);
        const tbody = document.getElementById('recentOrdersBody');
        tbody.innerHTML = '<tr><td colspan="7" class="loading">Failed to load orders</td></tr>';
    }
}

// Refresh specific chart
function refreshChart(chartName) {
    const dates = getDateRange(currentPeriod);
    
    if (chartName === 'salesTrend') {
        updateSalesTrendChart(dates);
    } else if (chartName === 'salesDist') {
        // Refresh sales distribution
        charts.salesDist.update();
    }
}

// Export report
function exportReport() {
    alert('Export functionality coming soon!');
    // TODO: Implement PDF/Excel export
}
