document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const calendarEl = document.getElementById('calendar');
    const slotList = document.getElementById('slot-list');
    const dateChosen = document.querySelector('.djangoAppt_date_chosen');
    const serviceDatetimeChosen = document.getElementById('service-datetime-chosen');
    const staffSelect = document.getElementById('staff_id');
    const appointmentForm = document.querySelector('.appointment-form');
    const submitButton = document.querySelector('.btn-submit-appointment');
    const errorMessageContainer = document.querySelector('.error-message');
    const slotContainer = document.querySelector('.slot-container');

    // State variables
    let selectedDate = rescheduledDate || null;
    let selectedSlot = null;
    let staffId = staffSelect ? staffSelect.value : null;
    if (staffId === "none") staffId = null;
    let nonWorkingDays = []; // This will store date strings like "2025-04-15"
    let previouslySelectedCell = null;
    let isRequestInProgress = false;

    // Initialize FullCalendar
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        initialDate: selectedDate,
        timeZone: timezone,
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
        dateClick: function(info) {
            const clickedDateStr = info.dateStr; // Format: YYYY-MM-DD

            // Check if the clicked date is a non-working day
            if (nonWorkingDays.includes(clickedDateStr)) {
                return; // Don't do anything if it's a non-working day
            }

            // If there's a previously selected cell, remove the class
            if (previouslySelectedCell) {
                previouslySelectedCell.classList.remove('selected-cell');
            }

            // Add the class to the currently clicked cell
            info.dayEl.classList.add('selected-cell');

            // Store the currently clicked cell
            previouslySelectedCell = info.dayEl;

            selectedDate = clickedDateStr;
            getAvailableSlots(clickedDateStr, staffId);
        },
        datesSet: function(info) {
            highlightSelectedDate();
        },
        selectAllow: function(info) {
            const dateStr = info.start.toISOString().split('T')[0]; // Format: YYYY-MM-DD

            // Disallow selection for non-working days
            if (nonWorkingDays.includes(dateStr)) {
                return false;
            }

            // Disallow dates before today
            return (info.start >= getDateWithoutTime(new Date()));
        },
        dayCellClassNames: function(info) {
            const dateStr = info.date.toISOString().split('T')[0]; // Format: YYYY-MM-DD

            // Add 'disabled-day' class to non-working days
            if (nonWorkingDays.includes(dateStr)) {
                return ['disabled-day'];
            }
            return [];
        }
    });

    // Initialize the calendar
    calendar.render();

    // Initial data loading
    if (selectedDate === null) {
        selectedDate = new Date().toISOString().split('T')[0]; // Today's date in YYYY-MM-DD format
    }

    // Fetch non-working days on initial load
    fetchNonWorkingDays(staffId);

    // Get available slots for initial date
    getAvailableSlots(selectedDate, staffId);

    // Event Listeners
    if (staffSelect) {
        staffSelect.addEventListener('change', function() {
            staffId = this.value;
            if (staffId === "none") staffId = null;

            let currentDate = selectedDate || new Date().toISOString().split('T')[0];

            fetchNonWorkingDays(staffId, function(newNonWorkingDays) {
                nonWorkingDays = newNonWorkingDays;
                calendar.render(); // Re-render calendar with updated non-working days
                getAvailableSlots(currentDate, staffId);
            });
        });
    }

    // Add event listener for the request next slot button
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('djangoAppt_btn-request-next-slot')) {
            const serviceId = event.target.getAttribute('data-service-id');
            requestNextAvailableSlot(serviceId);
        }
    });

    // Add event listener for the submit appointment button
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('btn-submit-appointment')) {
            const selectedSlotElement = document.querySelector('.djangoAppt_appointment-slot.selected');
            const selectedSlot = selectedSlotElement ? selectedSlotElement.textContent : '';
            const selectedDate = document.querySelector('.djangoAppt_date_chosen').textContent;

            if (!selectedSlot || !selectedDate) {
                alert(selectDateAndTimeAlertTxt);
                return;
            }

            if (selectedSlot && selectedDate) {
                submitAppointment(selectedSlot, selectedDate);
            } else {
                const warningContainer = document.querySelector('.warning-message');
                if (!warningContainer.querySelector('.submit-warning')) {
                    const warningPara = document.createElement('p');
                    warningPara.className = 'submit-warning';
                    warningPara.textContent = selectTimeSlotWarningTxt;
                    warningContainer.appendChild(warningPara);
                }
            }
        }
    });

    // Functions
    function fetchNonWorkingDays(staffId, callback) {
        if (!staffId || staffId === 'none') {
            nonWorkingDays = [];  // Reset nonWorkingDays
            calendar.render();   // Re-render the calendar
            if (callback) callback([]);
            return;  // Exit the function early
        }

        const formData = new FormData();
        formData.append('staff_member', staffId);

        fetch(getNonWorkingDaysURL, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching non-working days:', data.message);
                if (callback) callback([]);
            } else {
                // Updated to handle date strings array
                nonWorkingDays = data.non_working_days || [];
                console.log('Non-working days:', nonWorkingDays);
                calendar.render();
                if (callback) callback(nonWorkingDays);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (callback) callback([]);
        });
    }


    function getDateWithoutTime(dt) {
        const newDate = new Date(dt);
        newDate.setHours(0, 0, 0, 0);
        return newDate;
    }

    function convertTo24Hour(time12h) {
        const [time, modifier] = time12h.split(' ');
        let [hours, minutes] = time.split(':');

        if (hours === '12') {
            hours = '00';
        }

        if (modifier.toUpperCase() === 'PM') {
            hours = parseInt(hours, 10) + 12;
        }

        return `${hours}:${minutes}`;
    }

    function formatTime(date) {
        const hours = date.getHours();
        const minutes = date.getMinutes();
        return (hours < 10 ? '0' + hours : hours) + ':' + (minutes < 10 ? '0' + minutes : minutes);
    }

    function getAvailableSlots(selectedDate, staffId = null) {
        // Update the slot list with the available slots for the selected date
        const slotList = document.getElementById('slot-list');
        const slotContainer = document.querySelector('.slot-container');
        const errorMessageContainer = document.querySelector('.error-message');

        // Clear previous error messages and slots
        slotList.innerHTML = '';
        const noAvailabilityText = errorMessageContainer.querySelector('.djangoAppt_no-availability-text');
        if (noAvailabilityText) {
            noAvailabilityText.remove();
        }

        // Remove the "Next available date" message
        const nextAvailableDateElement = document.querySelector('.djangoAppt_next-available-date');
        if (nextAvailableDateElement) {
            nextAvailableDateElement.remove();
        }

        // Check if staffId is 'none', null, or undefined and display an error message
        if (staffId === 'none' || staffId === null || staffId === undefined) {
            console.log('No staff ID provided, displaying error message.');
            const errorMessage = document.createElement('p');
            errorMessage.className = 'djangoAppt_no-availability-text';
            errorMessage.textContent = noStaffMemberSelectedTxt;
            errorMessageContainer.appendChild(errorMessage);

            // Disable the "submit" button
            const submitButton = document.querySelector('.btn-submit-appointment');
            if (submitButton) submitButton.setAttribute('disabled', 'disabled');
            return;
        }

        // Send a fetch request to get the available slots for the selected date
        if (isRequestInProgress) {
            return; // Exit the function if a request is already in progress
        }

        isRequestInProgress = true;

        const formData = new FormData();
        formData.append('selected_date', selectedDate);
        formData.append('staff_member', staffId);

        fetch(availableSlotsAjaxURL, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            if (data.available_slots.length === 0) {
                const selectedDateObj = moment.tz(selectedDate, timezone);
                const selectedD = selectedDateObj.toDate();
                const today = new Date();
                today.setHours(0, 0, 0, 0);

                if (selectedD < today) {
                    // Show an error message
                    const errorPara = document.createElement('p');
                    errorPara.className = 'djangoAppt_no-availability-text';
                    errorPara.textContent = dateInPastErrorTxt;
                    errorMessageContainer.appendChild(errorPara);

                    if (!slotContainer.querySelector('.djangoAppt_btn-request-next-slot')) {
                        const requestButton = document.createElement('button');
                        requestButton.className = 'btn btn-danger djangoAppt_btn-request-next-slot';
                        requestButton.setAttribute('data-service-id', serviceId);
                        requestButton.textContent = requestNonAvailableSlotBtnTxt;
                        slotContainer.appendChild(requestButton);
                    }

                    // Disable the 'submit' button
                    const submitButton = document.querySelector('.btn-submit-appointment');
                    if (submitButton) submitButton.setAttribute('disabled', 'disabled');
                } else {
                    // Remove any existing no-availability-text
                    const existingNoAvailabilityText = errorMessageContainer.querySelector('.djangoAppt_no-availability-text');
                    if (existingNoAvailabilityText) {
                        existingNoAvailabilityText.remove();
                    }

                    // Add new no-availability-text
                    const noAvailabilityPara = document.createElement('p');
                    noAvailabilityPara.className = 'djangoAppt_no-availability-text';
                    noAvailabilityPara.textContent = data.message;
                    errorMessageContainer.appendChild(noAvailabilityPara);

                    // Check if the returned message is 'No availability'
                    if (data.message.toLowerCase() === 'no availability') {
                        if (!slotContainer.querySelector('.djangoAppt_btn-request-next-slot')) {
                            const requestButton = document.createElement('button');
                            requestButton.className = 'btn btn-danger djangoAppt_btn-request-next-slot';
                            requestButton.setAttribute('data-service-id', serviceId);
                            requestButton.textContent = requestNonAvailableSlotBtnTxt;
                            slotContainer.appendChild(requestButton);
                        }
                    } else {
                        const existingButton = document.querySelector('.djangoAppt_btn-request-next-slot');
                        if (existingButton) {
                            existingButton.remove();
                        }
                    }
                }
            } else {
                // Remove no-availability-text and request button
                const noAvailabilityText = document.querySelector('.djangoAppt_no-availability-text');
                if (noAvailabilityText) {
                    noAvailabilityText.remove();
                }

                const requestButton = document.querySelector('.djangoAppt_btn-request-next-slot');
                if (requestButton) {
                    requestButton.remove();
                }

                // Create unique slots array
                const uniqueSlots = [...new Set(data.available_slots)]; // remove duplicates

                // Add slots to the list
                uniqueSlots.forEach(slot => {
                    const li = document.createElement('li');
                    li.className = 'djangoAppt_appointment-slot';
                    li.textContent = slot;
                    slotList.appendChild(li);

                    // Add click event to each slot
                    li.addEventListener('click', function() {
                        // Remove selected class from all slots
                        document.querySelectorAll('.djangoAppt_appointment-slot').forEach(item => {
                            item.classList.remove('selected');
                        });

                        // Add selected class to clicked slot
                        this.classList.add('selected');

                        // Enable submit button
                        const submitButton = document.querySelector('.btn-submit-appointment');
                        if (submitButton) submitButton.removeAttribute('disabled');

                        // Update service datetime text
                        const serviceDatetimeChosen = document.getElementById('service-datetime-chosen');
                        if (serviceDatetimeChosen) {
                            serviceDatetimeChosen.textContent = data.date_chosen + ' ' + slot;
                        }
                    });
                });
            }

            // Update the date chosen
            const dateChosen = document.querySelector('.djangoAppt_date_chosen');
            if (dateChosen) {
                dateChosen.textContent = data.date_chosen;
            }

            const serviceDatetimeChosen = document.getElementById('service-datetime-chosen');
            if (serviceDatetimeChosen) {
                serviceDatetimeChosen.textContent = data.date_chosen;
            }

            isRequestInProgress = false;
        })
        .catch(error => {
            console.error('Error:', error);
            isRequestInProgress = false; // Reset the flag even if the request fails
        });
    }

    function requestNextAvailableSlot(serviceId) {
        const requestNextAvailableSlotURL = requestNextAvailableSlotURLTemplate.replace('0', serviceId);

        if (staffId === null) {
            return;
        }

        const formData = new FormData();
        formData.append('staff_member', staffId);

        fetch(requestNextAvailableSlotURL, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            // If there's an error, just log it and return
            let nextAvailableDateResponse = null;
            let formattedDate = null;

            if (data.error) {
                nextAvailableDateResponse = data.message;
            } else {
                // Set the date in the calendar to the next available date
                nextAvailableDateResponse = data.next_available_date;
                const selectedDateObj = moment.tz(nextAvailableDateResponse, timezone);
                const nextAvailableDate = selectedDateObj.toDate();
                formattedDate = new Intl.DateTimeFormat('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                }).format(nextAvailableDate);
            }

            // Find or create the next available date element
            let nextAvailableDateElement = document.querySelector('.djangoAppt_next-available-date');
            let nextAvailableDateText = data.error ? nextAvailableDateResponse : `Next available date: ${formattedDate}`;

            if (nextAvailableDateElement) {
                // Update existing element
                nextAvailableDateElement.textContent = nextAvailableDateText;
            } else {
                // Create new element
                nextAvailableDateElement = document.createElement('p');
                nextAvailableDateElement.className = 'djangoAppt_next-available-date';
                nextAvailableDateElement.textContent = nextAvailableDateText;

                const requestButton = document.querySelector('.djangoAppt_btn-request-next-slot');
                if (requestButton && requestButton.parentNode) {
                    requestButton.parentNode.insertBefore(nextAvailableDateElement, requestButton.nextSibling);
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    function submitAppointment(selectedSlot, selectedDate) {
        const startTime = convertTo24Hour(selectedSlot);

        // Convert the selectedDate string to a valid format
        const dateParts = selectedDate.split(', ');
        const monthDayYear = dateParts[1] + "," + dateParts[2];
        const formattedDate = new Date(monthDayYear + " " + startTime);

        const date = formattedDate.toISOString().slice(0, 10);
        const endTimeDate = new Date(formattedDate.getTime() + serviceDuration * 60000);
        const endTime = formatTime(endTimeDate);
        const reasonForRescheduling = document.getElementById('reason_for_rescheduling') ?
                                      document.getElementById('reason_for_rescheduling').value : '';

        const form = document.querySelector('.appointment-form');
        let formAction = rescheduledDate ? appointmentRescheduleURL : appointmentRequestSubmitURL;
        form.setAttribute('action', formAction);

        // Add or update hidden inputs
        updateOrCreateHiddenInput(form, 'appointment_request_id', appointmentRequestId);
        updateOrCreateHiddenInput(form, 'date', date);
        updateOrCreateHiddenInput(form, 'start_time', startTime);
        updateOrCreateHiddenInput(form, 'end_time', endTime);
        updateOrCreateHiddenInput(form, 'service', serviceId);
        updateOrCreateHiddenInput(form, 'reason_for_rescheduling', reasonForRescheduling);

        // Submit the form
        form.submit();
    }

    function updateOrCreateHiddenInput(form, name, value) {
        let input = form.querySelector(`input[name="${name}"]`);
        if (!input) {
            input = document.createElement('input');
            input.type = 'hidden';
            input.name = name;
            form.appendChild(input);
        }
        input.value = value;
    }

    function highlightSelectedDate() {
        setTimeout(function() {
            if (!selectedDate) return;

            const dateCell = document.querySelector(`.fc-daygrid-day[data-date='${selectedDate}']`);
            if (dateCell) {
                dateCell.classList.add('selected-cell');
                previouslySelectedCell = dateCell;
            }
        }, 10);
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
});