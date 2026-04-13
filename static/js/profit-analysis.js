// Profit Analysis Dashboard JavaScript

const BASE_API = (location.origin && location.origin.startsWith('http')) 
    ? (location.origin.replace(/\/$/, '') + '/api') 
    : 'http://127.0.0.1:8000/api';

let currentPeriod = 'daily';
let profitChart = null;
let distributionChart = null;
let comparisonChart = null;
let chartType = 'line'; // line or bar

// Get auth token
function getToken() {
    return localStorage.getItem('ap_token') || localStorage.getItem('authToken');
}

// Check if user is admin
function checkAdminAccess() {
    const user = JSON.parse(localStorage.getItem('ap_user') || localStorage.getItem('user') || '{}');
    console.log('Checking admin access for user:', user);
    
    // Check if user exists and is admin
    if (!user || !user.id) {
        console.log('No user found, redirecting to login');
        window.location.href = '/login/?next=/profit-analysis/';
        return false;
    }
    
    // Check if user is staff or superuser (admin)
    if (!user.is_staff && !user.is_superuser) {
        console.log('User is not admin, redirecting to home');
        alert('Access Denied: This page is only accessible to administrators.');
        window.location.href = '/';
        return false;
    }
    
    console.log('Admin access granted');
    return true;
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, checking admin access...');
    
    // Check admin access - MUST pass to continue
    if (!checkAdminAccess()) {
        console.log('Admin check failed, stopping initialization');
        return;
    }
    
    // Initialize charts
    console.log('Initializing charts...');
    initializeCharts();
    
    // Load data
    console.log('Loading profit data...');
    loadProfitData();
});

// Change period
function changePeriod(period) {
    currentPeriod = period;
    
    // Update active button
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-period="${period}"]`).classList.add('active');
    
    // Update subtitle
    const subtitles = {
        'daily': 'Daily profit for the last 30 days',
        'weekly': 'Weekly profit for the last 12 weeks',
        'monthly': 'Monthly profit for the last 12 months',
        'yearly': 'Yearly profit for the last 5 years'
    };
    document.getElementById('chartSubtitle').textContent = subtitles[period];
    
    // Reload data
    loadProfitData();
}

// Load profit data
async function loadProfitData() {
    console.log('Loading profit data...');
    try {
        showLoading();
        
        const token = getToken();
        console.log('Token:', token ? 'Found' : 'Not found');
        
        const dates = getDateRange(currentPeriod);
        console.log('Date range:', dates);
        
        const url = `${BASE_API}/billing/profit-analysis/?period=${currentPeriod}&start_date=${dates.start}&end_date=${dates.end}`;
        console.log('Fetching from:', url);
        
        const response = await fetch(url, {
            headers: {
                'Authorization': token ? `Token ${token}` : '',
                'Accept': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        
        if (response.status === 401 || response.status === 403) {
            console.error('Authentication failed');
            showError('Admin access required. Please login as admin.');
            // Don't redirect, just show error
            return;
        }
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Response error:', errorText);
            throw new Error(`Failed to load profit data: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Data received:', data);
        
        updateMetrics(data.summary);
        updateProfitChart(data.chart_data);
        updateDistributionChart(data.distribution);
        updateComparisonChart(data.comparison);
        updateTable(data.table_data);
        updateInsights(data.insights);
        
        console.log('Data loaded successfully');
        
    } catch (error) {
        console.error('Error loading profit data:', error);
        showError('Failed to load profit data: ' + error.message);
    }
}

// Get date range based on period
function getDateRange(period) {
    const end = new Date();
    const start = new Date();
    
    if (period === 'daily') {
        start.setDate(end.getDate() - 30);
    } else if (period === 'weekly') {
        start.setDate(end.getDate() - 84); // 12 weeks
    } else if (period === 'monthly') {
        start.setMonth(end.getMonth() - 12);
    } else if (period === 'yearly') {
        start.setFullYear(end.getFullYear() - 5);
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

// Update metrics cards
function updateMetrics(summary) {
    document.getElementById('totalProfit').textContent = 
        `₹${(summary.total_profit || 0).toLocaleString('en-IN')}`;
    document.getElementById('totalRevenue').textContent = 
        `₹${(summary.total_revenue || 0).toLocaleString('en-IN')}`;
    document.getElementById('totalCost').textContent = 
        `₹${(summary.total_cost || 0).toLocaleString('en-IN')}`;
    document.getElementById('profitMargin').textContent = 
        `${(summary.profit_margin || 0).toFixed(1)}%`;
    
    // Update change percentages
    updateChangeIndicator('profitChange', summary.profit_change || 0);
    updateChangeIndicator('revenueChange', summary.revenue_change || 0);
    updateChangeIndicator('costChange', summary.cost_change || 0);
    updateChangeIndicator('marginChange', summary.margin_change || 0);
}

// Update change indicator
function updateChangeIndicator(elementId, change) {
    const element = document.getElementById(elementId);
    const isPositive = change >= 0;
    
    element.textContent = `${isPositive ? '+' : ''}${change.toFixed(1)}%`;
    element.className = `metric-change ${isPositive ? 'positive' : 'negative'}`;
}

// Initialize charts
function initializeCharts() {
    // Main Profit Chart
    const profitCtx = document.getElementById('profitChart').getContext('2d');
    profitChart = new Chart(profitCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Profit',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: '#10b981',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                },
                {
                    label: 'Revenue',
                    data: [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                },
                {
                    label: 'Cost',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#f59e0b',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }
            ]
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
                    borderColor: '#10b981',
                    borderWidth: 2,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ₹' + context.parsed.y.toLocaleString('en-IN');
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

    // Distribution Chart
    const distCtx = document.getElementById('profitDistributionChart').getContext('2d');
    distributionChart = new Chart(distCtx, {
        type: 'doughnut',
        data: {
            labels: ['Spare Parts', 'Cars', 'Services'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    '#10b981',
                    '#667eea',
                    '#f59e0b'
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
                            return context.label + ': ₹' + context.parsed.toLocaleString('en-IN');
                        }
                    }
                }
            }
        }
    });

    // Comparison Chart
    const compCtx = document.getElementById('profitComparisonChart').getContext('2d');
    comparisonChart = new Chart(compCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Profit',
                data: [],
                backgroundColor: 'rgba(16, 185, 129, 0.8)',
                borderColor: '#10b981',
                borderWidth: 2,
                borderRadius: 8
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
                    callbacks: {
                        label: function(context) {
                            return 'Profit: ₹' + context.parsed.y.toLocaleString('en-IN');
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
}

// Update profit chart
function updateProfitChart(chartData) {
    if (!chartData || !profitChart) return;
    
    profitChart.data.labels = chartData.labels || [];
    profitChart.data.datasets[0].data = chartData.profit || [];
    profitChart.data.datasets[1].data = chartData.revenue || [];
    profitChart.data.datasets[2].data = chartData.cost || [];
    profitChart.update();
}

// Update distribution chart
function updateDistributionChart(distribution) {
    if (!distribution || !distributionChart) return;
    
    distributionChart.data.datasets[0].data = [
        distribution.spare_parts || 0,
        distribution.cars || 0,
        distribution.services || 0
    ];
    distributionChart.update();
}

// Update comparison chart
function updateComparisonChart(comparison) {
    if (!comparison || !comparisonChart) return;
    
    comparisonChart.data.labels = comparison.labels || [];
    comparisonChart.data.datasets[0].data = comparison.values || [];
    comparisonChart.update();
}

// Update table
function updateTable(tableData) {
    const tbody = document.getElementById('profitTableBody');
    tbody.innerHTML = '';
    
    if (!tableData || tableData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No data available</td></tr>';
        return;
    }
    
    tableData.forEach(row => {
        const tr = document.createElement('tr');
        const profitClass = row.profit >= 0 ? 'positive' : 'negative';
        
        tr.innerHTML = `
            <td><strong>${row.period}</strong></td>
            <td>₹${row.revenue.toLocaleString('en-IN')}</td>
            <td>₹${row.cost.toLocaleString('en-IN')}</td>
            <td><strong style="color: ${row.profit >= 0 ? '#10b981' : '#dc2626'}">₹${row.profit.toLocaleString('en-IN')}</strong></td>
            <td>${row.margin.toFixed(1)}%</td>
            <td>${row.orders}</td>
            <td>₹${row.avg_profit.toLocaleString('en-IN')}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Update insights
function updateInsights(insights) {
    const grid = document.getElementById('insightsGrid');
    grid.innerHTML = '';
    
    if (!insights || insights.length === 0) {
        grid.innerHTML = '<div class="insight-card"><p>No insights available yet.</p></div>';
        return;
    }
    
    insights.forEach(insight => {
        const card = document.createElement('div');
        card.className = `insight-card ${insight.type || ''}`;
        card.innerHTML = `
            <i class="fas ${insight.icon || 'fa-info-circle'}"></i>
            <p>${insight.message}</p>
        `;
        grid.appendChild(card);
    });
}

// Toggle chart type
function toggleChartType() {
    if (!profitChart) return;
    
    chartType = chartType === 'line' ? 'bar' : 'line';
    profitChart.config.type = chartType;
    profitChart.update();
}

// Refresh chart
function refreshChart() {
    loadProfitData();
}

// Refresh all data
function refreshData() {
    loadProfitData();
}

// Export profit report
function exportProfitReport() {
    alert('Export functionality coming soon!');
    // TODO: Implement PDF/Excel export
}

// Download table as CSV
function downloadTableCSV() {
    const table = document.getElementById('profitTable');
    let csv = [];
    
    // Headers
    const headers = [];
    table.querySelectorAll('thead th').forEach(th => {
        headers.push(th.textContent);
    });
    csv.push(headers.join(','));
    
    // Rows
    table.querySelectorAll('tbody tr').forEach(tr => {
        const row = [];
        tr.querySelectorAll('td').forEach(td => {
            row.push(td.textContent.replace(/,/g, ''));
        });
        if (row.length > 0) {
            csv.push(row.join(','));
        }
    });
    
    // Download
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `profit-analysis-${currentPeriod}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
}

// Show loading state
function showLoading() {
    document.getElementById('profitTableBody').innerHTML = 
        '<tr><td colspan="7" class="loading"><i class="fas fa-spinner fa-spin"></i> Loading data...</td></tr>';
    
    document.getElementById('insightsGrid').innerHTML = 
        '<div class="insight-card"><i class="fas fa-spinner fa-spin"></i><p>Analyzing data...</p></div>';
}

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #ef4444; color: white; padding: 16px 24px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 9999;';
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}

// Search table
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchTable');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#profitTableBody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
});
