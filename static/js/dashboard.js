let monthlyChartInstance = null;
let categoryChartInstance = null;
let cachedChartData = null;
let currentMonthlyChartType = 'bar';

function formatMonthName(str) {
    if (!str || typeof str !== 'string' || !str.includes('-')) return str;
    const parts = str.split('-');
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const monthIdx = parseInt(parts[1], 10) - 1;
    return (monthNames[monthIdx] || parts[1]) + ' ' + parts[0];
}

function formatCurrency(val) {
    return '₹' + Number(val).toLocaleString('en-IN', {
        minimumFractionDigits: 2, maximumFractionDigits: 2
    });
}

function updateTopCategoryDisplay(labels, values) {
    const topCatDisplay = document.getElementById('topCategoryDisplay');
    if (!topCatDisplay) return;

    if (labels && labels.length > 0 && values && values.length > 0) {
        // Since categories are ordered by total descending, the first element is the highest
        topCatDisplay.innerText = labels[0];
    } else {
        topCatDisplay.innerText = "No data";
    }
}

function renderCategoryChart(data, type = 'total') {
    const ctx = document.getElementById("categoryChart");
    const emptyState = document.getElementById("categoryChartEmpty");
    if (!ctx || !emptyState) return;

    let labels = type === 'total' ? data.categories : data.selected_month_categories;
    let values = type === 'total' ? data.category_totals : data.selected_month_category_totals;

    // Update the Top Category card text dynamically
    updateTopCategoryDisplay(labels, values);

    // --- NEW: Update Transactions Count dynamically ---
    const txnCountDisplay = document.getElementById('txnCountDisplay');
    if (txnCountDisplay) {
        txnCountDisplay.innerText = type === 'total' ? data.total_txn_count : data.selected_month_txn_count;
    }
    // ------------------------------------------------

    if (!labels || labels.length === 0) {
        ctx.style.display = 'none';
        emptyState.classList.remove('d-none');
        emptyState.classList.add('d-flex');
        return;
    } else {
        ctx.style.display = 'block';
        emptyState.classList.add('d-none');
        emptyState.classList.remove('d-flex');
    }

    const modernPalette = ['#2563eb', '#0d9488', '#f59e0b', '#10b981', '#0284c7', '#ec4899', '#f97316', '#64748b', '#84cc16', '#06b6d4', '#6366f1', '#475569'];
    const totalSpent = values.reduce((a, b) => a + b, 0);

    if (categoryChartInstance) categoryChartInstance.destroy();

    categoryChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: values, backgroundColor: modernPalette.slice(0, labels.length),
                borderWidth: 3, borderColor: '#ffffff', hoverOffset: 8, borderRadius: 5
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '72%',
            plugins: {
                legend: { position: "bottom", labels: { usePointStyle: true, pointStyle: 'circle', padding: 16, font: { family: "Arial, sans-serif", size: 12, weight: '500' }, color: '#4b5563' } },
                tooltip: {
                    backgroundColor: '#111827', titleColor: '#f9fafb', bodyColor: '#ffffff', padding: 12, cornerRadius: 10, boxPadding: 6,
                    callbacks: {
                        label: function(context) {
                            const val = context.raw || 0;
                            const pct = totalSpent > 0 ? ((val / totalSpent) * 100).toFixed(1) : 0;
                            return ` ${context.label}: ${formatCurrency(val)} (${pct}%)`;
                        }
                    }
                }
            },
            animation: { animateScale: true, animateRotate: true, duration: 900 }
        }
    });
}

function renderMonthlyChart(data, chartType = 'bar') {
    const canvas = document.getElementById("monthlyChart");
    if (!canvas) return;

    if (!data.months || data.months.length === 0) {
        canvas.parentElement.innerHTML = `
            <div class="d-flex flex-column align-items-center justify-content-center h-100 text-muted">
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="#cbd5e1" class="mb-2" viewBox="0 0 16 16">
                    <path d="M0 0h1v15h15v1H0zm10 3.5a.5.5 0 0 1 .5-.5h4a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-1 0V4.707l-4.146 4.147a.5.5 0 0 1-.708 0L7 6.707l-3.646 3.647a.5.5 0 0 1-.708-.708l4-4a.5.5 0 0 1 .708 0L9.5 7.793 13.293 4H10.5a.5.5 0 0 1-.5-.5"/>
                </svg>
                <span>No monthly data available</span>
            </div>`;
        return;
    }

    const ctx = canvas.getContext('2d');
    const formattedLabels = data.months.map(formatMonthName);

    let bgGradient = ctx.createLinearGradient(0, 0, 0, 240);
    if (chartType === 'bar') {
        bgGradient.addColorStop(0, 'rgba(37, 99, 235, 0.9)');
        bgGradient.addColorStop(1, 'rgba(96, 165, 250, 0.3)');
    } else {
        bgGradient.addColorStop(0, 'rgba(37, 99, 235, 0.25)');
        bgGradient.addColorStop(1, 'rgba(37, 99, 235, 0.01)');
    }

    if (monthlyChartInstance) monthlyChartInstance.destroy();

    monthlyChartInstance = new Chart(ctx, {
        type: chartType,
        data: {
            labels: formattedLabels,
            datasets: [{
                label: "Monthly Total", data: data.monthly_totals, backgroundColor: bgGradient,
                borderColor: '#2563eb', borderWidth: chartType === 'line' ? 3 : 1.5,
                borderRadius: chartType === 'bar' ? 10 : 0, borderSkipped: false, maxBarThickness: 54, fill: chartType === 'line',
                tension: 0.4, pointRadius: chartType === 'line' ? 6 : 0, pointBackgroundColor: '#ffffff',
                pointBorderColor: '#2563eb', pointBorderWidth: 3, pointHoverRadius: 9,
                pointHoverBackgroundColor: '#2563eb', pointHoverBorderColor: '#ffffff', pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, interaction: { intersect: false, mode: 'index' },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#111827', titleColor: '#f9fafb', bodyColor: '#ffffff', padding: 12, cornerRadius: 10,
                    callbacks: { label: function(context) { return ` Spent: ${formatCurrency(context.raw)}`; } }
                }
            },
            scales: {
                x: { grid: { display: false, drawBorder: false }, ticks: { color: '#6b7280', font: { size: 12, weight: '600' } } },
                y: {
                    beginAtZero: true, grid: { color: '#f1f5f9', drawBorder: false, borderDash: [5, 5] }, border: { display: false },
                    ticks: {
                        color: '#9ca3af', font: { size: 11 },
                        callback: function(val) {
                            if (val >= 1000) return '₹' + (val / 1000).toLocaleString() + 'k';
                            return '₹' + val;
                        }
                    }
                }
            },
            animation: { duration: 900, easing: 'easeOutQuart' }
        }
    });
}

function loadPieChartData(month) {
    if (month === 'total') {
        renderCategoryChart(cachedChartData, 'total');
    } else {
        fetch(`/api/chart-data?month=${month}`)
            .then(res => res.json())
            .then(data => renderCategoryChart(data, 'month'))
            .catch(err => console.error("Error fetching pie data:", err));
    }
}

function initDashboardCharts() {
    fetch("/api/chart-data")
        .then(response => response.json())
        .then(data => {
            cachedChartData = data;
            
            const select = document.getElementById("pieMonthSelect");
            const d = new Date();
            const currentMonthStr = d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, '0');

            if (select) {
                select.innerHTML = '';
                
                const optThis = document.createElement('option');
                optThis.value = currentMonthStr;
                optThis.textContent = "This Month";
                select.appendChild(optThis);

                const optTotal = document.createElement('option');
                optTotal.value = 'total';
                optTotal.textContent = "Lifetime Total";
                select.appendChild(optTotal);

                if (data.months) {
                    [...data.months].reverse().forEach(m => {
                        if (m !== currentMonthStr) {
                            const opt = document.createElement('option');
                            opt.value = m;
                            opt.textContent = formatMonthName(m);
                            select.appendChild(opt);
                        }
                    });
                }
                select.value = currentMonthStr;
            }

            renderCategoryChart(data, 'month');
            renderMonthlyChart(data, currentMonthlyChartType);
        })
        .catch(error => console.error("Chart error:", error));

    const btnBar = document.getElementById("btnChartBar");
    const btnLine = document.getElementById("btnChartLine");
    const pieSelect = document.getElementById("pieMonthSelect");

    if (btnBar && btnLine) {
        btnBar.addEventListener("click", function() {
            if (currentMonthlyChartType === 'bar') return;
            currentMonthlyChartType = 'bar';
            btnBar.classList.add("active");
            btnLine.classList.remove("active");
            if (cachedChartData) renderMonthlyChart(cachedChartData, 'bar');
        });

        btnLine.addEventListener("click", function() {
            if (currentMonthlyChartType === 'line') return;
            currentMonthlyChartType = 'line';
            btnLine.classList.add("active");
            btnBar.classList.remove("active");
            if (cachedChartData) renderMonthlyChart(cachedChartData, 'line');
        });
    }

    if (pieSelect) {
        pieSelect.addEventListener("change", function(e) {
            loadPieChartData(e.target.value);
        });
    }
}

document.addEventListener("DOMContentLoaded", initDashboardCharts);
