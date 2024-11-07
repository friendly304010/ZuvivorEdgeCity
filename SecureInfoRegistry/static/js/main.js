document.addEventListener('DOMContentLoaded', function() {
    const reportForm = document.getElementById('reportForm');
    const formSteps = document.querySelectorAll('.form-step');
    const progressItems = document.querySelectorAll('.progress-sidebar .list-group-item');
    let currentStep = 1;
    let currentReport = {};
    let deferredPrompt;

    // Form field groups
    const formFields = {
        1: ['perpetratorName', 'perpetratorEmail', 'perpetratorPhone', 'perpetratorXUsername', 'perpetratorTelegramUsername'],
        2: ['hairColor', 'eyeColor', 'skinColor', 'ethnicity', 'height', 'age'],
        3: ['vehicleLicensePlate', 'vehicleModel', 'vehicleMake'],
        4: ['locations', 'city', 'state', 'country', 'occupation', 'jobTitle', 'organizations'],
        5: ['incidentDetails', 'additionalInfo'],
        6: ['victimEmail']
    };

    // Clear form data for a specific step
    function clearStepData(step) {
        const fields = formFields[step] || [];
        fields.forEach(field => {
            const input = document.getElementById(field);
            if (input) {
                input.value = '';
                delete currentReport[field];
            }
        });
    }

    // Initialize form field listeners
    Object.values(formFields).flat().forEach(field => {
        const input = document.getElementById(field);
        if (input) {
            input.addEventListener('input', debounce(function() {
                updateField(field, input.value);
            }, 300));
        }
    });

    // Initialize identifier toggles
    const identifierToggles = document.querySelectorAll('.identifier-toggle');
    identifierToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const targetGroup = document.getElementById(this.dataset.target);
            if (targetGroup) {
                if (this.type === 'radio') {
                    document.querySelectorAll('[id$="VerificationGroup"]').forEach(group => {
                        group.style.display = 'none';
                        group.classList.remove('show');
                    });
                    if (this.checked) {
                        targetGroup.style.display = 'block';
                        targetGroup.classList.add('show');
                    }
                } else {
                    if (this.checked) {
                        targetGroup.style.display = 'block';
                        targetGroup.classList.add('show');
                    } else {
                        targetGroup.style.display = 'none';
                        targetGroup.classList.remove('show');
                        const inputs = targetGroup.querySelectorAll('input, textarea');
                        inputs.forEach(input => {
                            input.value = '';
                            updateField(input.id, '');
                        });
                    }
                }
            }
        });
    });

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Navigation Functions
    function showStep(step) {
        // Clear cached data from previous step
        clearStepData(currentStep);
        
        formSteps.forEach(formStep => {
            formStep.style.display = formStep.dataset.step == step ? 'block' : 'none';
        });

        progressItems.forEach(item => {
            if (item.dataset.step == step) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Update navigation buttons
        const prevButton = document.querySelector('.prev-step');
        const nextButton = document.querySelector('.next-step');
        const submitButton = document.querySelector('.submit-form');

        if (prevButton) prevButton.style.display = step > 1 ? 'block' : 'none';
        if (nextButton) nextButton.style.display = step < 6 ? 'block' : 'none';
        if (submitButton) submitButton.style.display = step == 6 ? 'block' : 'none';

        currentStep = step;
    }

    // Form validation
    function validateStep(step) {
        const fields = formFields[step];
        let isValid = true;

        fields.forEach(field => {
            const input = document.getElementById(field);
            if (!input) return;

            const group = input.closest('.identifier-group');
            if (!group || group.style.display !== 'none') {
                if (field === 'perpetratorName') return;

                if (step === 6) {
                    const emailVerification = document.getElementById('emailVerification');
                    if (emailVerification.checked && field === 'victimEmail') {
                        if (!validateEmail(input.value)) {
                            isValid = false;
                            input.classList.add('is-invalid');
                        }
                    }
                    return;
                }

                if (input.required && !input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');
                }

                if (input.value.trim()) {
                    if ((field === 'perpetratorEmail' || field === 'victimEmail') && !validateEmail(input.value)) {
                        isValid = false;
                        input.classList.add('is-invalid');
                    }

                    if (field === 'perpetratorPhone') {
                        const phoneRegex = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/;
                        if (!phoneRegex.test(input.value.replace(/\s+/g, ''))) {
                            isValid = false;
                            input.classList.add('is-invalid');
                        }
                    }

                    if (field === 'age') {
                        const age = parseInt(input.value);
                        if (isNaN(age) || age < 0 || age > 120) {
                            isValid = false;
                            input.classList.add('is-invalid');
                        }
                    }
                }
            }
        });

        if (step === 5 && !document.getElementById('incidentDetails').value.trim()) {
            isValid = false;
            document.getElementById('incidentDetails').classList.add('is-invalid');
        }

        return isValid;
    }

    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    // Event Listeners
    document.querySelector('.next-step')?.addEventListener('click', () => {
        if (validateStep(currentStep)) {
            showStep(currentStep + 1);
        }
    });

    document.querySelector('.prev-step')?.addEventListener('click', () => {
        showStep(currentStep - 1);
    });

    progressItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const step = parseInt(item.dataset.step);
            if (step < currentStep || validateStep(currentStep)) {
                showStep(step);
            }
        });
    });

    async function updateField(field, value) {
        if (value.trim() !== '') {
            currentReport[field] = value;
        } else {
            delete currentReport[field];
        }

        if (field === 'perpetratorXUsername' || field === 'perpetratorTelegramUsername') {
            if (value.trim() !== '' && !value.startsWith('@')) {
                value = '@' + value;
                document.getElementById(field).value = value;
                currentReport[field] = value;
            }
        }

        try {
            const response = await fetch('/update_report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ [field]: value }),
            });
            const result = await response.json();
            if (result.success) {
                updateOverlapCount(result.overlap_count);
                loadReports();
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    function updateOverlapCount(count) {
        const overlapCountElement = document.getElementById('overlapCount');
        if (overlapCountElement) {
            overlapCountElement.textContent = count;
        }
    }

    reportForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!validateStep(6)) {
            return;
        }

        try {
            const response = await fetch('/submit_report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(currentReport),
            });
            const result = await response.json();
            if (result.success) {
                alert(`Report submitted successfully.`);
                // Reset form and reload page to ensure fresh state
                reportForm.reset();
                currentReport = {};
                window.location.reload();
            } else {
                alert('Error submitting report');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while submitting the report');
        }
    });

    async function loadReports() {
        try {
            const response = await fetch('/get_reports', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(currentReport),
            });
            const reports = await response.json();
            const reportList = document.getElementById('reportList');
            if (reportList) {
                reportList.innerHTML = '';
                reports.forEach(report => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item';
                    li.textContent = `Report ID: ${report.id}, Perpetrator: ${report.perpetrator_name || 'Anonymous'}, Overlap Count: ${report.overlap_count}, Created: ${new Date(report.created_at).toLocaleString()}`;
                    reportList.appendChild(li);
                });
            }
        } catch (error) {
            console.error('Error loading reports:', error);
        }
    }

    // Initialize
    showStep(1);
    loadReports();
});
