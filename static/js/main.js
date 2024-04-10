// Keeps track of number of characters typed in course description
document.addEventListener('DOMContentLoaded', function () {
    var courseDescription = document.getElementById('course-description');
    var charCount = document.getElementById('char-count');
    var maxLength = 500;

    function updateCharCount() {
        var currentLength = courseDescription.value.length;
        var remaining = maxLength - currentLength;
        charCount.textContent = remaining >= 0 ? remaining : 0;

        // Truncate the value if it exceeds the max length
        if (currentLength > maxLength) {
            courseDescription.value = courseDescription.value.substr(0, maxLength);
            console.log("Input exceeded 500 characters and was truncated.");
        }
    }

    courseDescription.addEventListener('input', updateCharCount);
    updateCharCount(); // Initial call to set the correct initial value
});
