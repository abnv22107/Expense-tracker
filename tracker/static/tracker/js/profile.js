document.addEventListener('DOMContentLoaded', () => {
    const profileForm = document.getElementById('profileForm');
    const passwordForm = document.getElementById('passwordForm');
    const notificationForm = document.getElementById('notificationForm');

    if (profileForm) {
        profileForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            try {
                const formData = new FormData(profileForm);
                const response = await fetch('/tracker/profile/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: formData
                });

                if (response.ok) {
                    showToast('Profile updated successfully!', 'success');
                } else {
                    throw new Error('Failed to update profile');
                }
            } catch (error) {
                console.error('Error updating profile:', error);
                showToast('Error updating profile', 'danger');
            }
        });
    }

    if (passwordForm) {
        passwordForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            try {
                const formData = new FormData(passwordForm);
                const response = await fetch('/tracker/change-password/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: formData
                });

                if (response.ok) {
                    showToast('Password changed successfully!', 'success');
                    passwordForm.reset();
                } else {
                    throw new Error('Failed to change password');
                }
            } catch (error) {
                console.error('Error changing password:', error);
                showToast('Error changing password', 'danger');
            }
        });
    }

    if (notificationForm) {
        notificationForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            try {
                const formData = new FormData(notificationForm);
                const response = await fetch('/tracker/notification-settings/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: formData
                });

                if (response.ok) {
                    showToast('Notification settings updated successfully!', 'success');
                } else {
                    throw new Error('Failed to update notification settings');
                }
            } catch (error) {
                console.error('Error updating notification settings:', error);
                showToast('Error updating notification settings', 'danger');
            }
        });
    }
});

function showToast(message, type = 'success') {
    const toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    toastContainer.innerHTML = `
        <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    document.body.appendChild(toastContainer);
    const toast = new bootstrap.Toast(toastContainer.querySelector('.toast'));
    toast.show();
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
} 