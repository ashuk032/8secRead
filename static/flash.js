document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-messages .alert');
    flashMessages.forEach(function(message) {
        setTimeout(() => {
            message.classList.add('hide');
        }, 3000); // 3000 milliseconds = 3 seconds
    });
});
