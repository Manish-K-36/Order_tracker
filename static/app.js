document.addEventListener('DOMContentLoaded', () => {
    // --- Add Order Modal logic ---
    const modalAdd = document.getElementById('modal-add');
    const btnAdd = document.getElementById('btn-add-order');
    const closeAdd = document.getElementById('close-add');

    if (btnAdd && modalAdd && closeAdd) {
        btnAdd.addEventListener('click', () => {
            modalAdd.style.display = 'block';
        });

        closeAdd.addEventListener('click', () => {
            modalAdd.style.display = 'none';
        });
    }

    // --- Edit Order Modal logic ---
    const modalEdit = document.getElementById('modal-edit');
    const closeEdit = document.getElementById('close-edit');
    const editForm = document.getElementById('edit-form');
    const deleteForm = document.getElementById('delete-form');
    const editModalTitle = document.getElementById('edit-modal-title');

    // Edit form inputs
    const inputEditOrderNum = document.getElementById('edit-order-number');
    const inputEditClient = document.getElementById('edit-client-name');
    const inputEditEmail = document.getElementById('edit-email');
    const inputEditItems = document.getElementById('edit-item-details');
    const selectEditStatus = document.getElementById('edit-status');
    const inputEditEst = document.getElementById('edit-estimated-delivery');
    const inputEditCourier = document.getElementById('edit-courier-name');
    const inputEditTracking = document.getElementById('edit-tracking-number');
    const inputEditNotes = document.getElementById('edit-notes');

    if (closeEdit && modalEdit) {
        closeEdit.addEventListener('click', () => {
            modalEdit.style.display = 'none';
        });
    }

    // Bind Edit Button Clicks
    const editBtns = document.querySelectorAll('.btn-edit');
    editBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const orderNum = btn.getAttribute('data-ordernum');
            const client = btn.getAttribute('data-client');
            const email = btn.getAttribute('data-email');
            const items = btn.getAttribute('data-items');
            const status = btn.getAttribute('data-status');
            const notes = btn.getAttribute('data-notes');
            const courier = btn.getAttribute('data-courier');
            const tracking = btn.getAttribute('data-tracking');
            const est = btn.getAttribute('data-est');

            // Populate form
            editModalTitle.textContent = `Edit Order #${orderNum}`;
            inputEditOrderNum.value = orderNum;
            inputEditClient.value = client;
            inputEditEmail.value = email || '';
            inputEditItems.value = items;
            selectEditStatus.value = status;
            inputEditEst.value = est || '';
            inputEditCourier.value = courier || '';
            inputEditTracking.value = tracking || '';
            inputEditNotes.value = notes || '';

            // Update form actions with ID
            editForm.setAttribute('action', `/admin/update/${id}`);
            deleteForm.setAttribute('action', `/admin/delete/${id}`);

            // Open Modal
            modalEdit.style.display = 'block';
        });
    });

    // Close modals on clicking outside content area
    window.addEventListener('click', (e) => {
        if (e.target === modalAdd) {
            modalAdd.style.display = 'none';
        }
        if (e.target === modalEdit) {
            modalEdit.style.display = 'none';
        }
    });

    // --- Copy tracking link ---
    const toast = document.getElementById('toast');
    const copyLinkBtns = document.querySelectorAll('.btn-copy-link');

    copyLinkBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const orderNum = btn.getAttribute('data-ordernum');
            const trackingUrl = `${window.location.origin}/track/${orderNum}`;

            navigator.clipboard.writeText(trackingUrl).then(() => {
                showToast("Copied tracking link to clipboard!");
            }).catch(err => {
                console.error('Could not copy link: ', err);
            });
        });
    });

    // Toast show helper
    function showToast(message) {
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 2000);
    }

    // --- WhatsApp sharing ---
    const whatsappBtns = document.querySelectorAll('.btn-whatsapp');
    whatsappBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const client = btn.getAttribute('data-client');
            const status = btn.getAttribute('data-status');
            const orderNum = btn.getAttribute('data-ordernum');
            const trackingUrl = `${window.location.origin}/track/${orderNum}`;

            // Create pre-filled professional WhatsApp message
            const message = `Hello *${client}*,\n\nWe have updated the status of your order *#${orderNum}* to:\n👉 *${status}*\n\nYou can track the real-time progress of your order here:\n🔗 ${trackingUrl}\n\nThank you for business!`;
            
            const encodedMessage = encodeURIComponent(message);
            const whatsappUrl = `https://wa.me/?text=${encodedMessage}`;

            window.open(whatsappUrl, '_blank');
        });
    });
});
