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

// Populates number of turns options automatically
window.onload = function() {
    var select = document.getElementById("num-turns-select");
    for (var i = 1; i <= 20; i++) {
        var option = document.createElement("option");
        option.value = i;
        option.textContent = i;
        select.appendChild(option);
    }
};
