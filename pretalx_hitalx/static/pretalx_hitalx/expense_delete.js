(function () {
    var triggerRow = document.getElementById('hitalx-delete-trigger-row');
    var confirmRow = document.getElementById('hitalx-delete-confirm-row');
    if (!triggerRow || !confirmRow) return;

    document.getElementById('hitalx-delete-btn').addEventListener('click', function () {
        triggerRow.style.display = 'none';
        confirmRow.style.display = '';
    });
    document.getElementById('hitalx-delete-cancel-btn').addEventListener('click', function () {
        confirmRow.style.display = 'none';
        triggerRow.style.display = '';
    });
})();
