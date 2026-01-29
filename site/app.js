// RVA Figure Drawing Calendar - App JS

let allEvents = [];
let filteredEvents = [];
let currentMonth = new Date();

// DOM Elements
const eventsList = document.getElementById('events-list');
const eventsCalendar = document.getElementById('events-calendar');
const filterCost = document.getElementById('filter-cost');
const filterType = document.getElementById('filter-type');
const filterLocation = document.getElementById('filter-location');
const viewListBtn = document.getElementById('view-list');
const viewCalendarBtn = document.getElementById('view-calendar');
const lastUpdatedEl = document.getElementById('last-updated');
const calMonthEl = document.getElementById('cal-month');
const calDaysEl = document.getElementById('cal-days');
const calPrevBtn = document.getElementById('cal-prev');
const calNextBtn = document.getElementById('cal-next');

// Initialize
async function init() {
    try {
        const response = await fetch('../data/events.json');
        const data = await response.json();

        allEvents = data.events || [];

        // Update last updated timestamp
        if (data.lastUpdated) {
            const date = new Date(data.lastUpdated);
            lastUpdatedEl.textContent = date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit'
            });
        }

        // Populate location filter
        populateLocationFilter();

        // Apply filters and render
        applyFilters();

    } catch (error) {
        console.error('Failed to load events:', error);
        eventsList.innerHTML = '<p class="no-events">Failed to load events. Please try again later.</p>';
    }
}

function populateLocationFilter() {
    const locations = [...new Set(allEvents.map(e => e.location))].sort();
    locations.forEach(loc => {
        const option = document.createElement('option');
        option.value = loc;
        option.textContent = loc;
        filterLocation.appendChild(option);
    });
}

function applyFilters() {
    const costFilter = filterCost.value;
    const typeFilter = filterType.value;
    const locationFilter = filterLocation.value;
    const today = new Date().toISOString().split('T')[0];

    filteredEvents = allEvents.filter(event => {
        // Only show future events
        if (event.date < today) return false;

        // Cost filter
        if (costFilter === 'free' && event.costValue !== 0 && event.costValue !== null) {
            if (!event.cost.toLowerCase().includes('free')) return false;
        }
        if (costFilter === 'paid' && (event.costValue === 0 || event.cost.toLowerCase().includes('free'))) {
            return false;
        }

        // Type filter
        if (typeFilter !== 'all' && !event.tags.includes(typeFilter)) {
            return false;
        }

        // Location filter
        if (locationFilter !== 'all' && event.location !== locationFilter) {
            return false;
        }

        return true;
    });

    // Sort by date
    filteredEvents.sort((a, b) => {
        if (a.date !== b.date) return a.date.localeCompare(b.date);
        return (a.startTime || '').localeCompare(b.startTime || '');
    });

    renderList();
    renderCalendar();
}

function renderList() {
    if (filteredEvents.length === 0) {
        eventsList.innerHTML = '<p class="no-events">No upcoming events match your filters.</p>';
        return;
    }

    eventsList.innerHTML = filteredEvents.map(event => {
        const dateObj = new Date(event.date + 'T12:00:00');
        const dateStr = dateObj.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        });

        const timeStr = formatTimeRange(event.startTime, event.endTime);

        const tags = event.tags.map(tag =>
            `<span class="tag ${tag}">${tag.replace('-', ' ')}</span>`
        ).join('');

        const regStatus = event.registrationStatus && event.registrationStatus !== 'unknown'
            ? `<span class="registration-status ${event.registrationStatus}">${event.registrationStatus}</span>`
            : '';

        return `
            <article class="event-card">
                <div class="event-date">${dateStr}</div>
                <h2 class="event-title">
                    <a href="${event.url}" target="_blank">${event.title}</a>
                </h2>
                <div class="event-meta">
                    ${timeStr ? `<span class="event-time">${timeStr}</span>` : ''}
                    <span class="event-location">${event.location}</span>
                    <span class="event-cost">${event.cost}</span>
                </div>
                <div class="event-tags">
                    ${tags}
                    ${regStatus}
                </div>
            </article>
        `;
    }).join('');
}

function formatTimeRange(start, end) {
    if (!start) return '';

    const formatTime = (t) => {
        const [h, m] = t.split(':').map(Number);
        const ampm = h >= 12 ? 'pm' : 'am';
        const hour = h % 12 || 12;
        return m === 0 ? `${hour}${ampm}` : `${hour}:${m.toString().padStart(2, '0')}${ampm}`;
    };

    if (!end) return formatTime(start);
    return `${formatTime(start)} - ${formatTime(end)}`;
}

function renderCalendar() {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    calMonthEl.textContent = currentMonth.toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric'
    });

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startPad = firstDay.getDay();
    const totalDays = lastDay.getDate();

    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];

    // Get events for this month
    const monthEvents = {};
    filteredEvents.forEach(event => {
        const eventDate = new Date(event.date + 'T12:00:00');
        if (eventDate.getFullYear() === year && eventDate.getMonth() === month) {
            if (!monthEvents[event.date]) monthEvents[event.date] = [];
            monthEvents[event.date].push(event);
        }
    });

    let html = '';

    // Previous month padding
    const prevMonth = new Date(year, month, 0);
    for (let i = startPad - 1; i >= 0; i--) {
        const day = prevMonth.getDate() - i;
        html += `<div class="cal-day other-month"><span class="cal-day-num">${day}</span></div>`;
    }

    // Current month days
    for (let day = 1; day <= totalDays; day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const isToday = dateStr === todayStr;
        const dayEvents = monthEvents[dateStr] || [];

        const eventsHtml = dayEvents.slice(0, 2).map(e =>
            `<div class="cal-event" title="${e.title}" onclick="window.open('${e.url}', '_blank')">${e.location.split(' ')[0]}</div>`
        ).join('');

        const moreHtml = dayEvents.length > 2
            ? `<div class="cal-event" style="background:#666">+${dayEvents.length - 2} more</div>`
            : '';

        html += `
            <div class="cal-day ${isToday ? 'today' : ''}">
                <span class="cal-day-num">${day}</span>
                ${eventsHtml}${moreHtml}
            </div>
        `;
    }

    // Next month padding
    const endPad = (7 - ((startPad + totalDays) % 7)) % 7;
    for (let day = 1; day <= endPad; day++) {
        html += `<div class="cal-day other-month"><span class="cal-day-num">${day}</span></div>`;
    }

    calDaysEl.innerHTML = html;
}

// Event Listeners
filterCost.addEventListener('change', applyFilters);
filterType.addEventListener('change', applyFilters);
filterLocation.addEventListener('change', applyFilters);

viewListBtn.addEventListener('click', () => {
    viewListBtn.classList.add('active');
    viewCalendarBtn.classList.remove('active');
    eventsList.classList.remove('hidden');
    eventsCalendar.classList.add('hidden');
});

viewCalendarBtn.addEventListener('click', () => {
    viewCalendarBtn.classList.add('active');
    viewListBtn.classList.remove('active');
    eventsCalendar.classList.remove('hidden');
    eventsList.classList.add('hidden');
});

calPrevBtn.addEventListener('click', () => {
    currentMonth.setMonth(currentMonth.getMonth() - 1);
    renderCalendar();
});

calNextBtn.addEventListener('click', () => {
    currentMonth.setMonth(currentMonth.getMonth() + 1);
    renderCalendar();
});

// Start
init();
