// Search Function
// Function to get URL parameter by name
function getUrlParameter(name) {
    var urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// Populate search input with query from URL parameter
window.addEventListener('DOMContentLoaded', function() {
    var query = getUrlParameter('query');
    if (query) {
        document.getElementById('search-input').value = query;
    }
});

// Event listener for form submission on Enter key press
document.getElementById('search-input').addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault(); // Prevent default form submission
        var query = this.value.trim(); // Get the search query
        if (query !== '') {
            var isUser = document.body.classList.contains('user-dashboard');
            var searchRoute = isUser ? '/user_search' : '/user_search';
        
            window.location.href = searchRoute + '?query=' + encodeURIComponent(query); // Redirect to search page with query
        }
    }
});
