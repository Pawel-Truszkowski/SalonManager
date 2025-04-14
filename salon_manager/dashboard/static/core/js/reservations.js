document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const calendarEl = document.getElementById('calendar');
    const slotList = document.getElementById('slot-list');
    const dateChosen = document.querySelector('.djangoAppt_date_chosen');
    const serviceDatetimeChosen = document.getElementById('service-datetime-chosen');
    const staffSelect = document.getElementById('staff_id');
    const appointmentForm = document.querySelector('.appointment-form');
    const submitButton = document.querySelector('.btn-submit-appointment');
    const errorMessage = document.querySelector('.error-message');

    // State variables
    let selectedDate = null;
    let selectedSlot = null;
    let selectedStaffMember = staffSelect.value !== "none" ? staffSelect.value : null;
    let nonWorkingDays = [];
    let previouslySelectedCell = null;

    // Initialize FullCalendar
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        initialDate: selectedDate,
        locale: locale,
        headerToolbar: {
            left: 'title',
            right: 'prev,today,next',
        },
        height: '400px',
        themeSystem: 'bootstrap',
        nowIndicator: true,
        bootstrapFontAwesome: {
            close: 'fa-times',
            prev: 'fa-chevron-left',
            next: 'fa-chevron-right',
            prevYear: 'fa-angle-double-left',
            nextYear: 'fa-angle-double-right'
        },
        selectable: true,
        // select: handleDateSelect,
        dateClick: handleDateClick,
        datesSet: function (info) {
            highlightSelectedDate();
        },
        validRange: {
            start: new Date().toISOString().split('T')[0] // Only allow dates from today onwards
        },
        dayCellClassNames: function(info) {
            // Add class to non-working days
            const dateStr = info.date.toISOString().split('T')[0];
            if (nonWorkingDays.includes(dateStr)) {
                return ['disabled-day'];
            }
            return [];
        },
    });

    // Fetch non-working days on initial load
    fetchNonWorkingDays();

    calendar.render();

    // Event Listeners
    if (staffSelect) {
        staffSelect.addEventListener('change', function() {
            selectedStaffMember = this.value !== "none" ? this.value : null;
            fetchNonWorkingDays();
            if (selectedDate) {
                fetchAvailableSlots(selectedDate);
            }
            validateForm();
            clearError();
        });
    }

    // If rescheduling, pre-select date
    if (rescheduled_date) {
        const date = new Date(rescheduled_date);
        calendar.select(date);
        fetchAvailableSlots(formatDate(date));
    }

    // Form submission handling
    if (appointmentForm) {
        appointmentForm.addEventListener('submit', function(e) {
            e.preventDefault();

            if (!validateForm()) {
                return;
            }

            // Create form data
            const formData = new FormData(this);
            formData.append('service_id', serviceId);
            formData.append('date_selected', selectedDate);
            formData.append('time_selected', selectedSlot);
            formData.append('timezone', timezone);

            if (appointmentRequestId) {
                formData.append('appointment_request_id', appointmentRequestId);

                // If rescheduling, add reason
                const reasonInput = document.getElementById('reason_for_rescheduling');
                if (reasonInput) {
                    formData.append('reason_for_rescheduling', reasonInput.value);
                }

                // Submit reschedule request
                submitForm(appointmentRescheduleURL, formData);
            } else {
                // Submit new appointment request
                submitForm(appointmentRequestSubmitURL, formData);
            }
        });
    }

    // Functions
    function handleDateSelect(info) {
        const clickedDate = info.startStr;

        // Check if date is a non-working day
        if (nonWorkingDays.includes(clickedDate)) {
            calendar.unselect();
            showError(dateUnavailableTxt);
            clearError();
            return;
        }

        // Clear previous selection
        clearSlotSelection();

        // Fetch available slots
        fetchAvailableSlots(clickedDate);

        // Update selected date
        selectedDate = clickedDate;
        updateDateDisplay(clickedDate);

    }

    function handleDateClick(info) {
        const clickedDate = info.dateStr;

        // Check if date is a non-working day
        if (nonWorkingDays.includes(clickedDate)) {
            showError(dateUnavailableTxt);
            clearError();
            return;
        }

        // Add selected class to the clicked cell
        document.querySelectorAll('.selected-cell').forEach(el => {
            el.classList.remove('selected-cell');
        });
        info.dayEl.classList.add('selected-cell');

        // Select the date in the calendar
        calendar.select(info.date);
    }

    function fetchNonWorkingDays() {
        fetch(getNonWorkingDaysURL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                staff_id: selectedStaffMember
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                nonWorkingDays = data.non_working_days;
                console.log(nonWorkingDays);
                calendar.render(); // Re-render calendar with non-working days
            }
        })
        .catch(error => {
            console.error('Error fetching non-working days:', error);
        });
    }

    function fetchAvailableSlots(date) {
        if (!selectedStaffMember) {
            showError(noStaffMemberSelectedTxt);
            return;
        }

        // Clear the slot list
        slotList.innerHTML = '';

        // Show loading indicator
        slotList.innerHTML = '<li class="loading">Loading...</li>';

        fetch(availableSlotsAjaxURL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                date: date,
                staff_id: selectedStaffMember,
                service_id: serviceId,
                duration: serviceDuration
            })
        })
        .then(response => response.json())
        .then(data => {
            // Clear loading indicator
            slotList.innerHTML = '';

            if (data.success) {
                if (data.slots && data.slots.length > 0) {
                    // Display available slots
                    data.slots.forEach(slot => {
                        const slotItem = document.createElement('li');
                        const slotButton = document.createElement('div');
                        slotButton.className = 'djangoAppt_appointment-slot';
                        slotButton.textContent = slot;
                        slotButton.addEventListener('click', () => selectTimeSlot(slot, slotButton));
                        slotItem.appendChild(slotButton);
                        slotList.appendChild(slotItem);
                    });
                } else {
                    // No available slots
                    showNoAvailability(date);
                }
                clearError();
            } else {
                showError(data.message || 'Error fetching available slots');
            }
        })
        .catch(error => {
            console.error('Error fetching available slots:', error);
            showError('Error connecting to server.');
        });
    }

    function selectTimeSlot(slot, buttonElement) {
        // Clear previous selection
        document.querySelectorAll('.djangoAppt_appointment-slot').forEach(btn => {
            btn.classList.remove('selected');
        });

        // Mark selected
        buttonElement.classList.add('selected');

        // Update state
        selectedSlot = slot;

        // Update display
        updateDateTimeDisplay();

        // Enable submit button
        validateForm();
    }

    function showNoAvailability(date) {
        const messageItem = document.createElement('li');
        messageItem.className = 'djangoAppt_slot-item no-slots';
        messageItem.innerHTML = `<div class="djangoAppt_no-availability-text">No available slots for ${formatDateForDisplay(date)}</div>`;
        slotList.appendChild(messageItem);
    }

    function updateDateDisplay(date) {
        if (dateChosen) {
            dateChosen.textContent = formatDateForDisplay(date);
        }
    }

    function updateDateTimeDisplay() {
        if (serviceDatetimeChosen && selectedDate && selectedSlot) {
            serviceDatetimeChosen.textContent = `${formatDateForDisplay(selectedDate)} at ${selectedSlot}`;
        }
    }

    function clearSlotSelection() {
        selectedSlot = null;

        // Remove selected class from slots
        document.querySelectorAll('.djangoAppt_appointment-slot').forEach(btn => {
            btn.classList.remove('selected');
        });

        // Disable submit button
        submitButton.disabled = true;
    }

    function highlightSelectedDate() {
        setTimeout(function () {
            const dateCell = document.querySelector(`.fc-daygrid-day[data-date='${selectedDate}']`);
            if (dateCell) {
                dateCell.classList.add('selected-cell');
                previouslySelectedCell = dateCell;
            }
        }, 10);
    }

    function validateForm() {
        if (!selectedStaffMember || selectedStaffMember === "none") {
            submitButton.disabled = true;
            showError(noStaffMemberSelectedTxt);
            return false;
        }

        if (!selectedDate || !selectedSlot) {
            submitButton.disabled = true;
            showError(selectTimeSlotWarningTxt);
            return false;
        }

        // All validations passed
        submitButton.disabled = false;
        clearError();
        return true;
    }

    function showError(message) {
        if (errorMessage) {
            errorMessage.textContent = message;
            errorMessage.style.display = 'block';
        }
    }

    function clearError() {
        if (errorMessage) {
            errorMessage.textContent = '';
            errorMessage.style.display = 'none';
        }
    }

    function submitForm(url, formData) {
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = appointmentSuccessURL;
                clearError();
            } else {
                showError(data.message || 'Error submitting appointment.');
            }
        })
        .catch(error => {
            console.error('Error submitting form:', error);
            showError('Error connecting to server.');
        });
    }

    // Helper functions
    function formatDate(date) {
        // Format date as YYYY-MM-DD
        const d = new Date(date);
        return d.getFullYear() + '-' +
               String(d.getMonth() + 1).padStart(2, '0') + '-' +
               String(d.getDate()).padStart(2, '0');
    }

    function formatDateForDisplay(dateStr) {
        // Format date for display, e.g., "Monday, January 1, 2025"
        const date = new Date(dateStr);
        return date.toLocaleDateString(locale, {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    // Make requestNextAvailableSlot available globally
    window.requestNextAvailableSlot = function() {
        window.location.href = requestNextAvailableSlotURLTemplate.replace('0', serviceId);
    };
});

// Function to get CSRF token from cookies
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
