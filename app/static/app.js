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

    // Parse ISO format to datetime-local format (removes Z and milliseconds)
    function isoToDatetimeLocal(isoString) {
        if (!isoString) return '';
        // Remove 'Z' and anything after milliseconds
        const cleanStr = isoString.replace('Z', '').split('.')[0];
        return cleanStr;
    }

    // Populate form fields
    document.getElementById('editCategory').value = categoryId || '';
    document.getElementById('editDescription').value = description || '';
    document.getElementById('editStartTime').value = isoToDatetimeLocal(startTime);
    document.getElementById('editEndTime').value = isoToDatetimeLocal(endTime);

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

            // Convert datetime-local to ISO format with Z
            const convertToISO = (dtLocal) => {
                if (!dtLocal) return null;
                return new Date(dtLocal).toISOString();
            };

            formData.set('start_utc', convertToISO(startTime));
            if (endTime) {
                formData.set('end_utc', convertToISO(endTime));
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
    });
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
