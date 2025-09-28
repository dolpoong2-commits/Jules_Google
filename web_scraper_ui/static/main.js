document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const themeSelector = document.getElementById('theme');
    const body = document.body;
    const targetForm = document.getElementById('target-form');
    const targetList = document.getElementById('target-list');
    const scrapeButton = document.getElementById('scrape-button');
    const statusArea = document.getElementById('status-area');
    const resultList = document.getElementById('result-list');
    const downloadButton = document.getElementById('download-button');
    const savePathInput = document.getElementById('save-path');

    // --- State ---
    let selectedResults = new Set();

    // --- Functions ---

    // Function to change the theme
    function changeTheme(themeName) {
        body.className = ''; // Reset classes
        body.classList.add(`theme-${themeName}`);
        localStorage.setItem('selectedTheme', themeName);
    }

    // Function to fetch and display targets
    async function fetchTargets() {
        try {
            const response = await fetch('/api/targets');
            const targets = await response.json();
            targetList.innerHTML = ''; // Clear list
            targets.forEach(target => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <span>${target.url} (${target.type})</span>
                    <button class="delete-btn" data-id="${target.id}">삭제</button>
                `;
                targetList.appendChild(li);
            });
        } catch (error) {
            console.error('Error fetching targets:', error);
        }
    }

    // Function to handle target deletion
    async function deleteTarget(targetId) {
        try {
            const response = await fetch(`/api/targets/${targetId}`, { method: 'DELETE' });
            if (response.ok) {
                fetchTargets(); // Refresh the list
            } else {
                console.error('Failed to delete target');
            }
        } catch (error) {
            console.error('Error deleting target:', error);
        }
    }

    // Function to render results
    function renderResults(results) {
        resultList.innerHTML = '';
        if (results.length === 0) {
            resultList.innerHTML = '<li>수집된 결과가 없습니다.</li>';
            return;
        }
        results.forEach(result => {
            const li = document.createElement('li');
            li.innerHTML = `
                <input type="checkbox" class="result-checkbox" data-id="${result.id}">
                <div class="result-details">
                    <strong>${result.source_url}</strong>
                    <p>${result.error ? `오류: ${result.error}` : (result.content || '').substring(0, 200) + '...'}</p>
                </div>
            `;
            resultList.appendChild(li);
        });
    }

    // --- Event Listeners ---

    // Theme selector
    themeSelector.addEventListener('change', (event) => {
        changeTheme(event.target.value);
    });

    // Target form submission
    targetForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(targetForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('/api/targets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (response.ok) {
                targetForm.reset();
                fetchTargets();
            } else {
                console.error('Failed to add target');
            }
        } catch (error) {
            console.error('Error adding target:', error);
        }
    });

    // Deleting a target (using event delegation)
    targetList.addEventListener('click', (event) => {
        if (event.target.classList.contains('delete-btn')) {
            const targetId = event.target.getAttribute('data-id');
            deleteTarget(targetId);
        }
    });

    // Scrape button
    scrapeButton.addEventListener('click', async () => {
        statusArea.innerHTML = '<p>상태: 스크래핑 중...</p>';
        scrapeButton.disabled = true;
        downloadButton.disabled = true;

        try {
            const response = await fetch('/api/scrape', { method: 'POST' });
            const data = await response.json();
            statusArea.innerHTML = `<p>상태: ${data.message}</p>`;

            // Fetch and display results
            const resultsResponse = await fetch('/api/results');
            const results = await resultsResponse.json();
            renderResults(results);

        } catch (error) {
            statusArea.innerHTML = `<p>상태: 오류 발생 - ${error}</p>`;
            console.error('Scraping error:', error);
        } finally {
            scrapeButton.disabled = false;
        }
    });

    // Result checkbox handling (using event delegation)
    resultList.addEventListener('change', (event) => {
        if (event.target.classList.contains('result-checkbox')) {
            const resultId = parseInt(event.target.getAttribute('data-id'));
            if (event.target.checked) {
                selectedResults.add(resultId);
            } else {
                selectedResults.delete(resultId);
            }
            downloadButton.disabled = selectedResults.size === 0;
        }
    });

    // Download button
    downloadButton.addEventListener('click', async () => {
        if (selectedResults.size === 0) return;

        const data = {
            result_ids: Array.from(selectedResults),
            save_path: savePathInput.value || 'collected_data'
        };

        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            const responseData = await response.json();
            alert(responseData.message); // Simple feedback
        } catch (error) {
            console.error('Download error:', error);
            alert('다운로드 중 오류가 발생했습니다.');
        }
    });


    // --- Initial Load ---
    const savedTheme = localStorage.getItem('selectedTheme');
    if (savedTheme) {
        themeSelector.value = savedTheme;
        changeTheme(savedTheme);
    } else {
        changeTheme('sunrising');
    }

    fetchTargets(); // Initial fetch of targets
});