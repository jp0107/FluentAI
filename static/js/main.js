// Keeps track of number of characters typed in course description
document.addEventListener('DOMContentLoaded', function () {
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
});

// Allows tooltip functionality
document.addEventListener('DOMContentLoaded', function () {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
      var tooltip = new bootstrap.Tooltip(tooltipTriggerEl);
      
      // Show the tooltip
      tooltip.show();
  
      // Set a timeout to hide the tooltip after 5 seconds
      setTimeout(function () {
        tooltip.hide();
      }, 3000); // Adjust time as needed
    });
});
