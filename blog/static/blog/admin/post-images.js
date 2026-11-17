document.addEventListener('change', function (event) {
    const selected = event.target;
    if (!selected.matches('input[type="checkbox"][name^="images-"][name$="-is_main"]') || !selected.checked) {
        return;
    }
    document.querySelectorAll('input[type="checkbox"][name^="images-"][name$="-is_main"]').forEach(function (checkbox) {
        if (checkbox !== selected) checkbox.checked = false;
    });
});
