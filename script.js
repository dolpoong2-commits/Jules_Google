document.addEventListener('DOMContentLoaded', () => {
    const apiList = document.getElementById('api-list');
    const mainContent = document.getElementById('main-content');
    const searchInput = document.getElementById('searchInput');
    const themeSelect = document.getElementById('theme-select');
    let currentApiData = easyEDAApi;

    function applyTheme(theme) {
        document.body.className = `theme-${theme}`;
        localStorage.setItem('theme', theme);
    }

    themeSelect.addEventListener('change', (e) => {
        applyTheme(e.target.value);
    });

    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'default';
    themeSelect.value = savedTheme;
    applyTheme(savedTheme);

    // Tab switching
    const apiExplorerTab = document.getElementById('api-explorer-tab');
    const stockCheckerTab = document.getElementById('stock-checker-tab');
    const apiExplorerView = document.getElementById('api-explorer-view');
    const apiExplorerContent = document.getElementById('api-explorer-content');
    const stockCheckerView = document.getElementById('stock-checker-view');

    // Main navigation tabs
    apiExplorerTab.addEventListener('click', () => {
        apiExplorerTab.classList.add('active');
        stockCheckerTab.classList.remove('active');
        apiExplorerView.style.display = 'block';
        apiExplorerContent.style.display = 'block';
        stockCheckerView.style.display = 'none';
    });

    stockCheckerTab.addEventListener('click', () => {
        stockCheckerTab.classList.add('active');
        apiExplorerTab.classList.remove('active');
        stockCheckerView.style.display = 'block';
        apiExplorerView.style.display = 'none';
        apiExplorerContent.style.display = 'none';
    });

    // Stock checker tabs
    const lcscStockTab = document.getElementById('lcsc-stock-tab');
    const jlcpcbStockTab = document.getElementById('jlcpcb-stock-tab');
    const lcscStockContent = document.getElementById('lcsc-stock-content');
    const jlcpcbStockContent = document.getElementById('jlcpcb-stock-content');
    const searchLcscStockBtn = document.getElementById('searchLcscStockBtn');
    const stockResults = document.getElementById('stock-results');
    const exportCsvBtn = document.getElementById('exportCsvBtn');

    lcscStockTab.addEventListener('click', () => {
        lcscStockTab.classList.add('active');
        jlcpcbStockTab.classList.remove('active');
        lcscStockContent.style.display = 'block';
        jlcpcbStockContent.style.display = 'none';
        stockResults.innerHTML = ''; // Clear results
        exportCsvBtn.style.display = 'none';
    });

    jlcpcbStockTab.addEventListener('click', () => {
        jlcpcbStockTab.classList.add('active');
        lcscStockTab.classList.remove('active');
        jlcpcbStockContent.style.display = 'block';
        lcscStockContent.style.display = 'none';
        stockResults.innerHTML = ''; // Clear results
        exportCsvBtn.style.display = 'none';
    });

    searchLcscStockBtn.addEventListener('click', async () => {
        const partNumber = document.getElementById('lcscPartNumberInput').value.trim();
        if (!partNumber) {
            alert('Please enter an LCSC part number.');
            return;
        }

        stockResults.innerHTML = '<p>Searching...</p>';

        try {
            const response = await fetch(`/api/lcsc/search?q=${partNumber}`);
            const data = await response.json();

            if (data.success) {
                displayStockResults(data.result.products);
            } else {
                stockResults.innerHTML = `<p>Error: ${data.message || 'Failed to fetch data.'}</p>`;
            }
        } catch (error) {
            stockResults.innerHTML = `<p>An error occurred: ${error.message}</p>`;
        }
    });

    function displayStockResults(products) {
        if (!products || products.length === 0) {
            stockResults.innerHTML = '<p>No products found.</p>';
            exportCsvBtn.style.display = 'none';
            return;
        }

        let tableHtml = `
            <table>
                <thead>
                    <tr>
                        <th>LCSC Part #</th>
                        <th>Manufacturer</th>
                        <th>MFR Part #</th>
                        <th>Package</th>
                        <th>Stock</th>
                        <th>Price</th>
                    </tr>
                </thead>
                <tbody>
        `;
        products.forEach(product => {
            tableHtml += `
                <tr>
                    <td>${product.lcsc_part_number}</td>
                    <td>${product.brand_name_en}</td>
                    <td>${product.mfr_part_number}</td>
                    <td>${product.package_name_en}</td>
                    <td>${product.stock_number}</td>
                    <td>${product.product_price}</td>
                </tr>
            `;
        });
        tableHtml += '</tbody></table>';
        stockResults.innerHTML = tableHtml;
        exportCsvBtn.style.display = 'block';
    }

    // CSV Export
    exportCsvBtn.addEventListener('click', () => {
        const table = stockResults.querySelector('table');
        let csv = [];
        for (const row of table.rows) {
            const rowData = [];
            for (const cell of row.cells) {
                rowData.push(`"${cell.textContent.replace(/"/g, '""')}"`);
            }
            csv.push(rowData.join(','));
        }

        const blob = new Blob([csv.join('\\n')], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.setAttribute('hidden', '');
        a.setAttribute('href', url);
        a.setAttribute('download', 'lcsc_stock_export.csv');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });

    function displayApiDetails(api) {
        let paramsHtml = '<ul>';
        if (api.parameters && api.parameters.length > 0) {
            api.parameters.forEach(param => {
                paramsHtml += `<li><strong>${param.name}</strong> (${param.type}): ${param.description}</li>`;
            });
        } else {
            paramsHtml += '<li>No parameters</li>';
        }
        paramsHtml += '</ul>';

        mainContent.innerHTML = `
            <h2>${api.name}</h2>
            <p>${api.description}</p>
            <h3>Parameters</h3>
            ${paramsHtml}
            <h3>Example</h3>
            <pre>${api.example}</pre>
        `;
    }

    function populateApiList(apiData) {
        apiList.innerHTML = '';
        apiData.forEach(api => {
            const li = document.createElement('li');
            li.textContent = api.name;
            li.addEventListener('click', () => displayApiDetails(api));
            apiList.appendChild(li);
        });
    }

    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const filteredApi = easyEDAApi.filter(api => api.name.toLowerCase().includes(searchTerm));
        populateApiList(filteredApi);
    });

    populateApiList(currentApiData);
});