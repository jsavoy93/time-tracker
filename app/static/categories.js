/**
 * categories.js - Additional handling for categories page
 * (Included in categories.html for completeness)
 */

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const body = document.body;
    const themeToggle = document.getElementById('themeToggle');
    
    if (savedTheme === 'light') {
        body.classList.add('light-theme');
        if (themeToggle) themeToggle.textContent = '☀️ Light';
    } else {
        body.classList.remove('light-theme');
        if (themeToggle) themeToggle.textContent = '🌙 Dark';
    }
    
    // Setup theme toggle button
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = localStorage.getItem('theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            if (newTheme === 'light') {
                body.classList.add('light-theme');
                localStorage.setItem('theme', 'light');
                themeToggle.textContent = '☀️ Light';
            } else {
                body.classList.remove('light-theme');
                localStorage.setItem('theme', 'dark');
                themeToggle.textContent = '🌙 Dark';
            }
        });
    }

    // Handle edit category button clicks
document.addEventListener('DOMContentLoaded', function() {
    const editButtons = document.querySelectorAll('.edit-category-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const categoryId = this.dataset.categoryId;
            const categoryName = this.dataset.categoryName;
            openEditCategoryModal(categoryId, categoryName);
        });
    });
});
