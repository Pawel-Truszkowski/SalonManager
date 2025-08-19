/**
 * Utility functions for the application
 */

// Format a date object to YYYY-MM-DD string
function formatDateToYmd(date) {
    const d = new Date(date);
    return d.getFullYear() + '-' +
           String(d.getMonth() + 1).padStart(2, '0') + '-' +
           String(d.getDate()).padStart(2, '0');
}

// Format a time string (HH:MM) to a display format with AM/PM
function formatTimeForDisplay(timeStr) {
    // Convert 24-hour time to 12-hour time with AM/PM
    const [hours, minutes] = timeStr.split(':');
    const hour = parseInt(hours, 10);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour % 12 || 12; // Convert 0 to 12
    return `${hour12}:${minutes} ${ampm}`;
}

// Check if a date is in the past
function isDateInPast(dateStr) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const checkDate = new Date(dateStr);
    return checkDate < today;
}

// Calculate end time based on start time and duration in minutes
function calculateEndTime(startTimeStr, durationMinutes) {
    // Parse start time
    const [hours, minutes] = startTimeStr.split(':').map(Number);
    const startDate = new Date();
    startDate.setHours(hours, minutes, 0, 0);

    // Add duration
    const endDate = new Date(startDate.getTime() + durationMinutes * 60000);

    // Format end time
    const endHours = String(endDate.getHours()).padStart(2, '0');
    const endMinutes = String(endDate.getMinutes()).padStart(2, '0');

    return `${endHours}:${endMinutes}`;
}

// Check if a time slot overlaps with existing slots
function isTimeSlotOverlapping(startTime, endTime, existingSlots) {
    // Convert times to minutes for easier comparison
    const start = timeToMinutes(startTime);
    const end = timeToMinutes(endTime);

    for (const slot of existingSlots) {
        const slotStart = timeToMinutes(slot.start);
        const slotEnd = timeToMinutes(slot.end);

        // Check if slots overlap
        if ((start >= slotStart && start < slotEnd) ||
            (end > slotStart && end <= slotEnd) ||
            (start <= slotStart && end >= slotEnd)) {
            return true;
        }
    }

    return false;
}

// Convert time string to minutes since midnight
function timeToMinutes(timeStr) {
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + minutes;
}

// Format price with currency symbol
function formatPrice(price, currencySymbol = '$') {
    return `${currencySymbol}${parseFloat(price).toFixed(2)}`;
}

// Format duration in minutes to hours and minutes
function formatDuration(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;

    if (hours > 0 && mins > 0) {
        return `${hours} hour${hours > 1 ? 's' : ''} ${mins} minute${mins > 1 ? 's' : ''}`;
    } else if (hours > 0) {
        return `${hours} hour${hours > 1 ? 's' : ''}`;
    } else {
        return `${mins} minute${mins > 1 ? 's' : ''}`;
    }
}

// Debounce function to limit how often a function can be called
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
