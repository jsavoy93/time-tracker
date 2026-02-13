/**
 * Main app.js - Handles modal interactions and session editing
 */

// Theme switching
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
}

function setTheme(theme) {
    const body = document.body;
    const themeToggle = document.getElementById('themeToggle');
    
    if (theme === 'light') {
        body.classList.add('light-theme');
        localStorage.setItem('theme', 'light');
        if (themeToggle) themeToggle.textContent = '☀️ Light';
    } else {
        body.classList.remove('light-theme');
        localStorage.setItem('theme', 'dark');
        if (themeToggle) themeToggle.textContent = '🌙 Dark';
    }
}

function toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

function openEditModal(sessionId, categoryId, description, startTime, endTime) {
    const modal = document.getElementById('editModal');
    const form = document.getElementById('editForm');
    const errorDiv = document.getElementById('editError');

    // Set form action
    form.action = `/sessions/${sessionId}/edit`;

    // Convert UTC ISO string to datetime-local format
    // datetime-local inputs expect YYYY-MM-DDTHH:MM:SS in local browser time
    function utcToDatetimeLocal(isoString) {
        if (!isoString) return '';
        try {
            // Remove Z and parse as UTC
            let cleanStr = isoString.replace('Z', '').replace(/\.\d+$/, '');  // Remove ALL digits after decimal
            // Parse the components
            const match = cleanStr.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/);
            if (!match) return '';
            
            const [, year, month, day, hours, minutes, seconds] = match;
            
            // Create UTC date
            const utcDate = new Date(Date.UTC(year, parseInt(month) - 1, day, hours, minutes, seconds));
            
            // Get offset and apply it
            const offset = new Date().getTimezoneOffset();
            const localDate = new Date(utcDate.getTime() - offset * 60 * 1000);
            
            // Format with zero padding
            const y = localDate.getUTCFullYear();
            const m = String(localDate.getUTCMonth() + 1).padStart(2, '0');
            const d = String(localDate.getUTCDate()).padStart(2, '0');
            const h = String(localDate.getUTCHours()).padStart(2, '0');
            const min = String(localDate.getUTCMinutes()).padStart(2, '0');
            const s = String(localDate.getUTCSeconds()).padStart(2, '0');
            
            return `${y}-${m}-${d}T${h}:${min}:${s}`;
        } catch (e) {
            console.error('Error converting UTC to datetime-local:', e, isoString);
            return '';
        }
    }

    // Populate form fields
    document.getElementById('editCategory').value = categoryId || '';
    document.getElementById('editDescription').value = description || '';
    document.getElementById('editStartTime').value = utcToDatetimeLocal(startTime);
    document.getElementById('editEndTime').value = utcToDatetimeLocal(endTime);

    errorDiv.innerHTML = '';
    errorDiv.classList.remove('show');

    modal.style.display = 'block';
}

function closeEditModal() {
    const modal = document.getElementById('editModal');
    modal.style.display = 'none';
}

function openEditCategoryModal(categoryId, categoryName) {
    const modal = document.getElementById('editCategoryModal');
    const form = document.getElementById('editCategoryForm');
    const errorDiv = document.getElementById('editCategoryError');

    form.action = `/categories/${categoryId}/edit`;
    document.getElementById('editCategoryName').value = categoryName;

    errorDiv.innerHTML = '';
    errorDiv.classList.remove('show');

    modal.style.display = 'block';
}

function closeEditCategoryModal() {
    const modal = document.getElementById('editCategoryModal');
    modal.style.display = 'none';
}

function openImportModal() {
    const modal = document.getElementById('importModal');
    const resultDiv = document.getElementById('importResult');
    resultDiv.innerHTML = '';
    resultDiv.classList.remove('show');
    document.getElementById('importData').value = '';
    modal.style.display = 'block';
}

function closeImportModal() {
    const modal = document.getElementById('importModal');
    modal.style.display = 'none';
}

// Handle edit form submission
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    initializeTheme();
    
    // Setup theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // Handle edit session button clicks
    const editSessionButtons = document.querySelectorAll('.edit-session-btn');
    editSessionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const sessionId = this.dataset.sessionId;
            const categoryId = this.dataset.categoryId;
            const description = this.dataset.description;
            const startTime = this.dataset.startTime;
            const endTime = this.dataset.endTime;
            openEditModal(sessionId, categoryId, description, startTime, endTime);
        });
    });

    const editForm = document.getElementById('editForm');
    if (editForm) {
        editForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(editForm);
            const startTime = formData.get('start_utc');
            const endTime = formData.get('end_utc');

            // Basic validation
            if (!startTime) {
                showEditError('Start time is required.');
                return;
            }

            if (endTime) {
                const start = new Date(startTime);
                const end = new Date(endTime);
                if (end <= start) {
                    showEditError('End time must be after start time.');
                    return;
                }
            }

            // Convert datetime-local (local time) to UTC ISO format
            const datetimeLocalToUTC = (dtLocal) => {
                if (!dtLocal) return null;
                try {
                    // datetime-local is YYYY-MM-DDTHH:MM:SS in browser local time
                    // Create a Date object from this string (browser treats it as local)
                    const localDate = new Date(dtLocal);
                    
                    // Get timezone offset
                    const tzOffset = localDate.getTimezoneOffset() * 60000;
                    
                    // Convert to UTC by adding the offset back
                    const utcDate = new Date(localDate.getTime() + tzOffset);
                    
                    // Return ISO format with Z
                    const isoString = utcDate.toISOString();
                    // Remove milliseconds
                    return isoString.replace(/\.\d{3}Z$/, 'Z');
                } catch (e) {
                    console.error('Error converting datetime-local to UTC:', e);
                    return null;
                }
            };

            formData.set('start_utc', datetimeLocalToUTC(startTime));
            if (endTime) {
                formData.set('end_utc', datetimeLocalToUTC(endTime));
            }

            try {
                const response = await fetch(editForm.action, {
                    method: 'POST',
                    body: formData,
                });

                if (response.ok) {
                    closeEditModal();
                    window.location.reload();
                } else {
                    const error = await response.text();
                    showEditError(error);
                }
            } catch (err) {
                showEditError(`Error: ${err.message}`);
            }
        });
    }

    const editCategoryForm = document.getElementById('editCategoryForm');
    if (editCategoryForm) {
        editCategoryForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(editCategoryForm);
            const name = formData.get('name').trim();

            if (!name) {
                showEditCategoryError('Category name cannot be empty.');
                return;
            }

            try {
                const response = await fetch(editCategoryForm.action, {
                    method: 'POST',
                    body: formData,
                });

                if (response.ok) {
                    closeEditCategoryModal();
                    window.location.reload();
                } else {
                    const error = await response.text();
                    showEditCategoryError(error);
                }
            } catch (err) {
                showEditCategoryError(`Error: ${err.message}`);
            }
        });
    }

    // Handle add category form
    const addCategoryForm = document.querySelector('form[action="/categories/add"]');
    if (addCategoryForm) {
        addCategoryForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(addCategoryForm);
            const errorDiv = document.getElementById('addError');

            try {
                const response = await fetch('/categories/add', {
                    method: 'POST',
                    body: formData,
                });

                if (response.ok) {
                    window.location.reload();
                } else {
                    const error = await response.text();
                    errorDiv.innerHTML = error;
                    errorDiv.classList.add('show');
                }
            } catch (err) {
                errorDiv.innerHTML = `Error: ${err.message}`;
                errorDiv.classList.add('show');
            }
        });
    }

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        const editModal = document.getElementById('editModal');
        if (event.target === editModal) {
            closeEditModal();
        }

        const editCategoryModal = document.getElementById('editCategoryModal');
        if (event.target === editCategoryModal) {
            closeEditCategoryModal();
        }

        const importModal = document.getElementById('importModal');
        if (event.target === importModal) {
            closeImportModal();
        }
    });

    // Handle import form
    const importForm = document.getElementById('importForm');
    if (importForm) {
        importForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(importForm);
            const resultDiv = document.getElementById('importResult');

            try {
                const response = await fetch('/import', {
                    method: 'POST',
                    body: formData,
                });

                const result = await response.json();

                if (response.ok) {
                    resultDiv.innerHTML = result.message;
                    resultDiv.className = 'success-message show';
                    setTimeout(() => {
                        closeImportModal();
                        window.location.reload();
                    }, 1500);
                } else {
                    resultDiv.innerHTML = result.detail || 'Import failed';
                    resultDiv.className = 'error-message show';
                }
            } catch (err) {
                resultDiv.innerHTML = `Error: ${err.message}`;
                resultDiv.className = 'error-message show';
            }
        });
    }
});

function showEditError(message) {
    const errorDiv = document.getElementById('editError');
    errorDiv.innerHTML = message;
    errorDiv.classList.add('show');
}

function showEditCategoryError(message) {
    const errorDiv = document.getElementById('editCategoryError');
    errorDiv.innerHTML = message;
    errorDiv.classList.add('show');
}
