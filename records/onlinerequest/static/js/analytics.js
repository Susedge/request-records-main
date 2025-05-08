// Global variables
let documentChart;
let requestTable;
let documentStatsData = [];

// Analytics Chart Functions
function loadStats() {
    fetch(`/api/request-stats/?filter=${$('#timeFilter').val()}`)
        .then(response => response.json())
        .then(data => {
            documentStatsData = data.document_stats; // Store the data globally
            updateDocumentChart(data.document_stats);
            updateProcessingTimes(data.processing_times);
        })
        .catch(error => {
            console.error('Error loading analytics data:', error);
        });
}

function updateDocumentChart(stats) {
    const ctx = document.getElementById('documentChart');
    
    if (documentChart) {
        documentChart.destroy();
    }
    
    // Create colors array based on the number of items
    const colors = generateChartColors(stats.length);
    
    documentChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: stats.map(s => s.request__document__description),
            datasets: [{
                data: stats.map(s => s.count),
                backgroundColor: colors
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.formattedValue || '';
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((context.raw / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function updateProcessingTimes(times) {
    const container = document.getElementById('processingTimes');
    
    if (times.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No processing data available for the selected time period.</div>';
        return;
    }
    
    container.innerHTML = times.map(t => `
        <div class="alert alert-${t.status === 'completed' ? 'success' : 'warning'} mb-2">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>Request #${t.request_id}</strong>: ${t.days} days, ${t.hours} hours
                </div>
                <span class="badge bg-${t.status === 'completed' ? 'success' : 'warning'}">
                    ${t.status}
                </span>
            </div>
        </div>
    `).join('');
}

// Helper function to generate nice chart colors
function generateChartColors(count) {
    const baseColors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#6f42c1', '#fd7e14', '#20c9a6', '#5a5c69', '#858796'
    ];
    
    // If we have more items than colors, repeat colors with different opacity
    const colors = [];
    for (let i = 0; i < count; i++) {
        if (i < baseColors.length) {
            colors.push(baseColors[i]);
        } else {
            // Recycle colors with different opacity
            const colorIndex = i % baseColors.length;
            const opacity = 0.6 - (Math.floor(i / baseColors.length) * 0.2);
            colors.push(adjustColorOpacity(baseColors[colorIndex], opacity));
        }
    }
    
    return colors;
}

function adjustColorOpacity(hex, opacity) {
    // Convert hex to RGB
    let r = parseInt(hex.slice(1, 3), 16);
    let g = parseInt(hex.slice(3, 5), 16);
    let b = parseInt(hex.slice(5, 7), 16);
    
    // Return RGBA color
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

// Format status with appropriate styling
function formatStatus(cell) {
    const value = cell.getValue();
    let className = '';
    
    switch(value) {
        case 'Pending':
            className = 'status-pending';
            break;
        case 'Processing':
            className = 'status-processing';
            break;
        case 'Completed':
            className = 'status-completed';
            break;
        case 'Rejected':
            className = 'status-rejected';
            break;
        default:
            className = '';
    }
    
    return `<span class="${className}">${value}</span>`;
}

function initializeTable() {
    // Define column configuration with all columns visible by default
    const columns = [
        {title: "Ref. No.", field: "reference_number", headerHozAlign: "center", hozAlign: "center", width: 120, headerTooltip: true},
        {title: "Date Requested", field: "date_requested", headerHozAlign: "center", hozAlign: "center", sorter: "date", sorterParams: {format: "MMM DD, YYYY"}, width: 170, headerTooltip: true},
        {title: "Client Type", field: "client_type", headerHozAlign: "center", hozAlign: "center", width: 140, headerTooltip: true},
        {title: "Requested By", field: "requested_by", headerHozAlign: "center", width: 200, headerTooltip: true},
        {title: "Contact Details", field: "contact_details", headerHozAlign: "center", width: 160, headerTooltip: true},
        {title: "Email", field: "email", headerHozAlign: "center", width: 220, headerTooltip: true},
        {title: "Service Type", field: "service_type", headerHozAlign: "center", width: 200, headerTooltip: true},
        {title: "Purpose", field: "purpose", headerHozAlign: "center", width: 200, headerTooltip: true},
        {title: "Status", field: "status", headerHozAlign: "center", hozAlign: "center", formatter: formatStatus, width: 130, headerTooltip: true},
        {title: "Schedule", field: "schedule", headerHozAlign: "center", hozAlign: "center", width: 140, headerTooltip: true},
        {title: "Date Completed", field: "date_completed", headerHozAlign: "center", hozAlign: "center", width: 170, headerTooltip: true},
        {title: "Date Released", field: "date_released", headerHozAlign: "center", hozAlign: "center", width: 170, headerTooltip: true},
        {title: "Process Time", field: "processing_time", headerHozAlign: "center", hozAlign: "center", width: 160, headerTooltip: true}
    ];
    
    // Initialize Tabulator with horizontal scrolling and no column collapsing
    requestTable = new Tabulator("#requestTable", {
        ajaxURL: "/api/request-details/",
        ajaxResponse: function(url, params, response) {
            return response;
        },
        layout: "fitData",  // Fit columns to their data
        layoutColumnsOnNewData: true,
        columns: columns,
        initialSort: [{column: "date_requested", dir: "desc"}],
        height: "auto",
        maxHeight: "70vh",
        pagination: true,
        paginationSize: 15,
        paginationSizeSelector: [10, 15, 25, 50, 100, true],
        movableColumns: true,
        printAsHtml: true,
        printHeader: "<h3>Request Records</h3>",
        printFooter: "<p>Printed on " + new Date().toLocaleString() + "</p>",
        placeholder: "No Data Available",
        responsiveLayout: false,  // Disable responsive layout
        headerFilterPlaceholder: "Filter...",
        persistenceMode: "local",
        persistence: true,
        persistenceID: "requestTableState",
    });
    
    return requestTable;
}

// Date range filtering
function setupDateRangeFiltering(table) {
    $('#applyDateFilter').on('click', function() {
        const fromDate = $('#dateFrom').val();
        const toDate = $('#dateTo').val();
        
        if (fromDate || toDate) {
            // Apply the filter when both dates are selected
            table.setFilter(function(data) {
                if (!data.date_requested) return true;
                
                // Convert the date string to Date object for comparison (format: "MMM DD, YYYY")
                const dateParts = data.date_requested.split(' ');
                const month = dateParts[0];
                const day = parseInt(dateParts[1].replace(',', ''));
                const year = parseInt(dateParts[2]);
                
                const months = {
                    'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 
                    'May': 4, 'Jun': 5, 'Jul': 6, 'Aug': 7,
                    'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
                };
                
                const rowDate = new Date(year, months[month], day);
                
                let valid = true;
                if (fromDate && !isNaN(new Date(fromDate))) {
                    valid = valid && rowDate >= new Date(fromDate);
                }
                
                if (toDate && !isNaN(new Date(toDate))) {
                    valid = valid && rowDate <= new Date(toDate);
                }
                
                return valid;
            });
        }
    });
    
    $('#clearDateFilter').on('click', function() {
        $('#dateFrom, #dateTo').val('');
        table.clearFilter();
        showToast('Date filters cleared');
    });
}


// Set up export functionality
function setupExportButtons(table) {
    // Export to CSV
    document.getElementById("export-csv").addEventListener("click", function() {
        table.download("csv", "reports_summary.csv", {
            sheetName: "Reports Summary"
        });
        showToast('CSV exported successfully');
    });
    
    // Export to Excel
    document.getElementById("export-excel").addEventListener("click", function() {
        table.download("xlsx", "reports_summary.xlsx", {
            sheetName: "Reports Summary"
        });
        showToast('Excel file exported successfully');
    });
    
    // Export to PDF with smaller fonts and bold title
    document.getElementById("export-pdf").addEventListener("click", function() {
        table.download("pdf", "reports_summary.pdf", {
            orientation: "landscape",
            title: "Reports Summary",
            autoTable: {
                styles: {
                    headerColor: [41, 128, 185],
                    fontStyle: 'bold',
                    fontSize: 7,
                    cellPadding: 3
                },
                headStyles: {
                    fontSize: 8,
                    fontStyle: 'bold',
                    halign: 'center'
                },
                columnStyles: {
                    id: {fontStyle: 'bold'}
                },
                margin: {top: 45, left: 10, right: 10},
                didDrawPage: function(data) {
                    let doc = data.doc;
                    doc.setFontSize(14);
                    doc.setFont(undefined, 'bold');
                    doc.text("Request Records", data.settings.margin.left, 20);
                    
                    doc.setFontSize(10);
                    doc.setFont(undefined, 'normal');
                    doc.text("Generated on: " + new Date().toLocaleString(), data.settings.margin.left, 25);
                }
            }
        });
        showToast('PDF exported successfully');
    });
    
}

// Handle tab switching (ensure table is correctly sized when tab becomes visible)
function setupTabSwitching(table) {
    $('button[data-bs-toggle="tab"]').on('shown.bs.tab', function (e) {
        if (e.target.id === 'request-data-tab') {
            table.redraw(true); // Force a full redraw of the table
        } else if (e.target.id === 'charts-tab') {
            loadStats(); // Load chart data when switching to charts tab
        }
    });
}

// Setup global search functionality
function setupSearchFunctionality(table) {
    // Search as you type with debounce
    let searchTimeout;
    $('#searchInput').on('input', function() {
        const searchValue = $(this).val();
        
        // Clear any pending timeouts to avoid multiple rapid searches
        clearTimeout(searchTimeout);
        
        // Set a short timeout to avoid searching on every keystroke
        searchTimeout = setTimeout(function() {
            if (searchValue === '') {
                table.clearFilter();
            } else {
                performSearch(table, searchValue);
            }
        }, 300); // 300ms delay for smoother typing experience
    });
    
    // Keep the button click handler as an alternative
    $('#searchButton').on('click', function() {
        const searchValue = $('#searchInput').val();
        performSearch(table, searchValue);
    });
    
    // Keep the Enter key handler for compatibility
    $('#searchInput').on('keyup', function(e) {
        if (e.key === 'Enter') {
            const searchValue = $(this).val();
            performSearch(table, searchValue);
        }
    });
}

// Perform the actual search across all columns
function performSearch(table, value) {
    if (value === '') {
        table.clearFilter();
        return;
    }
    
    // Apply filter to search across all fields
    table.setFilter(function(data) {
        // Search in all object properties
        for (let key in data) {
            // Skip if property doesn't exist or is null
            if (!data[key]) continue;
            
            // Convert both to lowercase for case-insensitive search
            if (String(data[key]).toLowerCase().includes(value.toLowerCase())) {
                return true;
            }
        }
        return false;
    });
}

// Function to export chart data as CSV
function exportChartAsCSV() {
    console.log('Exporting chart as CSV...');
    if (documentStatsData.length === 0) {
        showToast('No data available to export', true);
        return;
    }
    
    const csvRows = [];
    const headers = ['Document Type', 'Count', 'Percentage'];
    csvRows.push(headers.join(','));
    
    const total = documentStatsData.reduce((sum, item) => sum + item.count, 0);
    
    documentStatsData.forEach(item => {
        const percentage = ((item.count / total) * 100).toFixed(2);
        const rowData = [
            `"${item.request__document__description}"`,
            item.count,
            `${percentage}%`
        ];
        csvRows.push(rowData.join(','));
    });
    
    // Create a total row
    csvRows.push(['"TOTAL"', total, '100.00%'].join(','));
    
    // Add a timestamp of when the report was generated
    const timestamp = new Date().toLocaleString();
    csvRows.push([`"Report generated on: ${timestamp}"`].join(','));
    
    // Create and download the CSV file
    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'document_requests_summary.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Function to export chart data as Excel
function exportChartAsExcel() {
    console.log('Exporting chart as Excel...');
    if (documentStatsData.length === 0) {
        showToast('No data available to export', true);
        return;
    }
    
    // Create a workbook with a worksheet
    const wb = XLSX.utils.book_new();
    
    // Prepare data for the worksheet
    const wsData = [['Document Type', 'Count', 'Percentage']];
    
    const total = documentStatsData.reduce((sum, item) => sum + item.count, 0);
    
    documentStatsData.forEach(item => {
        const percentage = ((item.count / total) * 100).toFixed(2);
        wsData.push([
            item.request__document__description,
            item.count,
            `${percentage}%`
        ]);
    });
    
    // Add a total row
    wsData.push(['TOTAL', total, '100.00%']);
    
    // Add a timestamp
    wsData.push([]);
    wsData.push([`Report generated on: ${new Date().toLocaleString()}`]);
    
    // Create the worksheet
    const ws = XLSX.utils.aoa_to_sheet(wsData);
    
    // Add the worksheet to the workbook
    XLSX.utils.book_append_sheet(wb, ws, 'Document Requests');
    
    // Generate the Excel file and trigger download
    XLSX.writeFile(wb, 'document_requests_summary.xlsx');
}

// Function to export chart data as PDF
function exportChartAsPDF() {
    try {
        console.log('Exporting chart as PDF...');
        if (!documentStatsData || documentStatsData.length === 0) {
            showToast('No data available to export', true);
            return;
        }
        
        console.log('Document stats data:', documentStatsData);
        
        // Create PDF document
        const { jsPDF } = window.jspdf;
        if (!jsPDF) {
            console.error('jsPDF not available');
            showToast('PDF export library not loaded. Please try again.', true);
            return;
        }
        
        const doc = new jsPDF();
        
        // Add title
        doc.setFontSize(16);
        doc.setFont(undefined, 'bold');
        doc.text('Document Requests Summary', 14, 20);
        
        // Add timestamp
        doc.setFontSize(10);
        doc.setFont(undefined, 'normal');
        doc.text(`Report generated on: ${new Date().toLocaleString()}`, 14, 30);
        
        // Calculate total
        const total = documentStatsData.reduce((sum, item) => sum + item.count, 0);
        
        // Prepare data for the table
        const tableData = documentStatsData.map(item => {
            const percentage = ((item.count / total) * 100).toFixed(2);
            return [
                item.request__document__description,
                item.count,
                `${percentage}%`
            ];
        });
        
        // Add total row
        tableData.push(['TOTAL', total, '100.00%']);
        
        // Create the PDF table
        doc.autoTable({
            head: [['Document Type', 'Count', 'Percentage']],
            body: tableData,
            startY: 40,
            styles: {
                fontSize: 10,
                cellPadding: 3
            },
            headStyles: {
                fillColor: [41, 128, 185],
                textColor: 255,
                fontStyle: 'bold'
            },
            alternateRowStyles: {
                fillColor: [240, 240, 240]
            }
        });
        
        // Add pie chart image
        if (documentChart) {
            try {
                const chartImg = documentChart.toBase64Image();
                doc.addPage();
                doc.setFontSize(14);
                doc.setFont(undefined, 'bold');
                doc.text('Document Requests Chart', 14, 20);
                doc.addImage(chartImg, 'JPEG', 20, 30, 170, 150);
            } catch (e) {
                console.error('Error adding chart to PDF:', e);
            }
        }
        
        // Save the PDF
        doc.save('document_requests_summary.pdf');
        
        // Show success toast after export
        showToast('PDF exported successfully');
    } catch (error) {
        console.error('Error exporting to PDF:', error);
        showToast('Error exporting to PDF: ' + error.message, true);
    }
}

// Set up export buttons for the chart - make sure to properly attach event handlers
function setupChartExportButtons() {
    // First, remove any existing event listeners (to prevent duplicates)
    const csvBtn = document.getElementById('export-chart-csv');
    const excelBtn = document.getElementById('export-chart-excel');
    const pdfBtn = document.getElementById('export-chart-pdf');
    
    // Clone and replace elements to remove all event listeners
    if (csvBtn) {
        const newCsvBtn = csvBtn.cloneNode(true);
        csvBtn.parentNode.replaceChild(newCsvBtn, csvBtn);
        
        // Add the event listener to the new button
        newCsvBtn.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent any default behavior
            e.stopPropagation(); // Stop event bubbling
            exportChartAsCSV();
        });
    }
    
    if (excelBtn) {
        const newExcelBtn = excelBtn.cloneNode(true);
        excelBtn.parentNode.replaceChild(newExcelBtn, excelBtn);
        
        newExcelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            exportChartAsExcel();
        });
    }
    
    if (pdfBtn) {
        const newPdfBtn = pdfBtn.cloneNode(true);
        pdfBtn.parentNode.replaceChild(newPdfBtn, pdfBtn);
        
        newPdfBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            exportChartAsPDF();
        });
    }
}

// Then, in the document ready function, add:
$(document).ready(function() {
    // Set a flag to track if we've already set up the buttons
    if (!window.chartExportButtonsInitialized) {
        setupChartExportButtons();
        window.chartExportButtonsInitialized = true;
    }
    
    // Load charts data
    $('#timeFilter').change(loadStats);
    loadStats();
    
    // Initialize and setup Tabulator table
    const table = initializeTable();
    setupDateRangeFiltering(table);
    setupExportButtons(table);
    setupChartExportButtons();
    setupSearchFunctionality(table); // Add this line
    setupTabSwitching(table);
    
    // Handle window resize
    $(window).resize(function() {
        if (table) {
            table.redraw(true);
        }
    });
    
    // Make sure this function is called
    setupChartExportButtons();
    
    // Add a direct check to verify the buttons exist
    console.log('CSV Button exists:', $('#export-chart-csv').length > 0);
    console.log('Excel Button exists:', $('#export-chart-excel').length > 0);
    console.log('PDF Button exists:', $('#export-chart-pdf').length > 0);
});
