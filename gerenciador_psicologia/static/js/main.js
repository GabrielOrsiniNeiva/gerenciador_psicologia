// Initialize Feather icons
document.addEventListener('DOMContentLoaded', function() {
    feather.replace();

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Phone number formatting
    const phoneInput = document.getElementById('phone');

function confirmDelete(paymentId) {
    return confirm('Tem certeza que deseja excluir este registro?');
}
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 0) {
                if (value.length <= 2) {
                    value = `(${value}`;
                } else if (value.length <= 6) {
                    value = `(${value.substring(0,2)}) ${value.substring(2)}`;
                } else if (value.length <= 10) {
                    value = `(${value.substring(0,2)}) ${value.substring(2,6)}-${value.substring(6)}`;
                } else {
                    value = `(${value.substring(0,2)}) ${value.substring(2,7)}-${value.substring(7,11)}`;
                }
            }
            e.target.value = value;
        });
    }

    // Toggle payment date field on appointment form
    const statusSelect = document.getElementById('status');
    if (statusSelect) {
        togglePaymentDate(statusSelect.value);
        statusSelect.addEventListener('change', (event) => {
            togglePaymentDate(event.target.value);
        });
    }
});

function togglePaymentDate(status) {
    const paymentDateWrapper = document.getElementById('payment_date_wrapper');
    const paymentDateInput = document.getElementById('payment_date');
    if (paymentDateWrapper) {
        if (status === 'Paga') {
            paymentDateWrapper.style.display = 'block';
            paymentDateInput.required = true;
        } else {
            paymentDateWrapper.style.display = 'none';
            paymentDateInput.required = false;
        }
    }
}
