document.addEventListener('DOMContentLoaded', function () {
    // Keeps track of number of characters typed in course description
    const textAreas = document.querySelectorAll('textarea[data-max-length]');

    function updateCharCount(textArea) {
        const maxLength = textArea.getAttribute('data-max-length');
        const charCountId = `char-count-${textArea.id}`;
        const charCountEl = document.getElementById(charCountId);
        const currentLength = textArea.value.length;
        const remaining = maxLength - currentLength;
        charCountEl.textContent = remaining >= 0 ? remaining : 0;

        if (currentLength > maxLength) {
            textArea.value = textArea.value.substr(0, maxLength);
            console.log(`Input exceeded ${maxLength} characters and was truncated.`);
        }
    }

    textAreas.forEach((textArea) => {
        updateCharCount(textArea); // Initial update for each text area
        textArea.addEventListener('input', () => updateCharCount(textArea));
    });

    // Tooltips initialization
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        var tooltip = new bootstrap.Tooltip(tooltipTriggerEl);
        setTimeout(function () {
            tooltip.hide();
        }, 5000); // Adjust time as needed
    });

    // Modal field reset
    var allModals = document.querySelectorAll('.modal');
    allModals.forEach(function(modal) {
        modal.addEventListener('hidden.bs.modal', function () {
            var textFields = modal.querySelectorAll('textarea, input[type="text"], input[type="date"], input[type="time"], select');
            textFields.forEach(function(field) {
                field.value = '';
                if (field.tagName === 'SELECT') {
                    field.selectedIndex = 0;
                }
                if (field.hasAttribute('data-max-length')) {
                    updateCharCount(field); // Update char count for fields after clearing
                }
            });

            // Explicitly call updateCharCount for textareas or input fields within the modal
            var charCountAreas = modal.querySelectorAll('textarea[data-max-length], input[type="text"][data-max-length]');
            charCountAreas.forEach(updateCharCount);
        });
    });
});
