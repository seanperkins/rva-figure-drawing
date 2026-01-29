// RVA Figure Drawing Calendar - App JS

let allEvents = [];
let filteredEvents = [];
let currentMonth = new Date();

// Color map for event sources
const sourceColors = {
    visarts: '#2563eb',    // Blue
    studio23: '#7c3aed',   // Purple
    artspace: '#059669',   // Green
    artworks: '#d97706',   // Amber
    vmfa: '#dc2626',       // Red
    eventbrite: '#6366f1'  // Indigo
};

// Utility: Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility: Escape attribute values
function escapeAttr(text) {
    if (!text) return '';
    return text.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

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
        const response = await fetch('data/events.json');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
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

        // Set up calendar subscription link
        setupSubscribeLink();

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

function setupSubscribeLink() {
    const subscribeBtn = document.getElementById('subscribe-btn');
    const copyBtn = document.getElementById('copy-url-btn');
    const hint = document.getElementById('subscribe-hint');

    // Build calendar URLs
    let basePath = window.location.pathname;
    if (basePath.endsWith('/')) {
        basePath = basePath.slice(0, -1);
    } else if (basePath.includes('.')) {
        basePath = basePath.replace(/\/[^/]*$/, '');
    }
    const calendarUrl = `${window.location.origin}${basePath}/data/calendar.ics`;
    const webcalUrl = calendarUrl.replace(/^https?:/, 'webcal:');

    // Subscribe button uses webcal:// protocol to open calendar app directly
    if (subscribeBtn) {
        subscribeBtn.href = webcalUrl;
    }

    // Copy URL button for users who prefer manual subscription
    if (copyBtn) {
        copyBtn.addEventListener('click', async () => {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                try {
                    await navigator.clipboard.writeText(calendarUrl);
                    hint.textContent = 'URL copied! Paste into your calendar app\'s "Add by URL" option.';
                    hint.style.color = '#166534';
                    return;
                } catch (err) {
                    // Fall through to fallback
                }
            }
            // Fallback: show URL for manual copy
            hint.textContent = calendarUrl;
            hint.style.color = 'var(--text-muted)';
        });
    }
}

function applyFilters() {
    const costFilter = filterCost.value;
    const typeFilter = filterType.value;
    const locationFilter = filterLocation.value;
    const today = new Date().toISOString().split('T')[0];

    filteredEvents = allEvents.filter(event => {
        // Only show future events
        if (event.date < today) return false;

        // Cost filter - simplified logic with defensive checks
        const costText = event.cost ? event.cost.toLowerCase() : '';
        const isFreeEvent = event.costValue === 0 ||
                           event.costValue === null ||
                           costText.includes('free');

        if (costFilter === 'free' && !isFreeEvent) return false;
        if (costFilter === 'paid' && isFreeEvent) return false;

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

    eventsList.innerHTML = filteredEvents.map((event, index) => {
        const dateObj = new Date(event.date + 'T12:00:00');
        const dateStr = dateObj.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        });

        const timeStr = formatTimeRange(event.startTime, event.endTime);

        const tags = event.tags.map(tag => {
            const safeTag = escapeHtml(tag);
            const safeClass = tag.replace(/[^a-z0-9-]/gi, '');
            return `<span class="tag ${safeClass}">${safeTag.replace('-', ' ')}</span>`;
        }).join('');

        const regStatus = event.registrationStatus && event.registrationStatus !== 'unknown'
            ? `<span class="registration-status ${escapeAttr(event.registrationStatus)}">${escapeHtml(event.registrationStatus)}</span>`
            : '';

        const mapsUrl = event.address
            ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(event.address)}`
            : null;

        const locationHtml = mapsUrl
            ? `<a href="${mapsUrl}" target="_blank" rel="noopener noreferrer">${escapeHtml(event.location)}</a>`
            : escapeHtml(event.location);

        const sourceColor = sourceColors[event.source] || '#888';

        return `
            <article class="event-card" data-event-index="${index}" style="border-left-color: ${sourceColor}">
                <div class="event-header">
                    <div class="event-date">${escapeHtml(dateStr)}</div>
                    <div class="add-to-cal-wrapper">
                        <button class="add-to-cal" onclick="toggleCalendarMenu(${index})" aria-label="Add to calendar options">
                            <span aria-hidden="true">📅</span>
                            <span class="add-to-cal-text">Add to Calendar</span>
                        </button>
                        <div class="calendar-menu" id="cal-menu-${index}" role="menu">
                            <a href="${getGoogleCalendarUrl(event)}" target="_blank" rel="noopener noreferrer" role="menuitem">Google Calendar</a>
                            <button onclick="downloadEventICS(${index})" role="menuitem">Download ICS</button>
                        </div>
                    </div>
                </div>
                <h2 class="event-title">
                    <a href="${escapeAttr(event.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(event.title)}</a>
                </h2>
                <div class="event-meta">
                    ${timeStr ? `<span class="event-time">${escapeHtml(timeStr)}</span>` : ''}
                    <span class="event-location">${locationHtml}</span>
                    <span class="event-cost">${escapeHtml(event.cost)}</span>
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

// ICS line folding per RFC 5545 (max 75 octets per line)
function foldICSLine(line) {
    const maxLen = 75;
    if (line.length <= maxLen) return line;

    let result = line.substring(0, maxLen);
    let pos = maxLen;
    while (pos < line.length) {
        result += '\r\n ' + line.substring(pos, pos + maxLen - 1);
        pos += maxLen - 1;
    }
    return result;
}

// Add hours to a time string (HH:MM format)
function addHoursToTime(timeStr, hours) {
    if (!timeStr) return null;
    const [h, m] = timeStr.split(':').map(Number);
    const newH = (h + hours) % 24;
    return `${String(newH).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function generateICS(event) {
    const formatICSDate = (date, time) => {
        const d = date.replace(/-/g, '');
        const t = time ? time.replace(':', '') + '00' : '000000';
        return d + 'T' + t;
    };

    const escapeICS = (str) => {
        if (!str) return '';
        return str
            .replace(/\\/g, '\\\\')
            .replace(/;/g, '\\;')
            .replace(/,/g, '\\,')
            .replace(/\n/g, '\\n');
    };

    const uid = `${event.date}-${(event.startTime || '0000').replace(':', '')}-${event.source}@rvafiguredrawing`;
    const dtstart = formatICSDate(event.date, event.startTime);

    // If no end time, default to 1 hour after start (avoid zero-duration events)
    const endTime = event.endTime || addHoursToTime(event.startTime, 1) || event.startTime;
    const dtend = formatICSDate(event.date, endTime);

    const location = event.address
        ? `${event.location}, ${event.address}`
        : event.location;

    const description = [
        event.description,
        event.cost ? `Cost: ${event.cost}` : '',
        event.url ? `Register: ${event.url}` : ''
    ].filter(Boolean).join('\\n\\n');

    const lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//RVA Figure Drawing//Calendar//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'BEGIN:VEVENT',
        `UID:${uid}`,
        `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, '').split('.')[0]}Z`,
        `DTSTART:${dtstart}`,
        `DTEND:${dtend}`,
        foldICSLine(`SUMMARY:${escapeICS(event.title)}`),
        foldICSLine(`LOCATION:${escapeICS(location)}`),
        foldICSLine(`DESCRIPTION:${escapeICS(description)}`),
        event.url ? `URL:${event.url}` : '',
        'END:VEVENT',
        'END:VCALENDAR'
    ].filter(Boolean);

    return lines.join('\r\n');
}

function getGoogleCalendarUrl(event) {
    const formatGoogleDate = (date, time) => {
        const d = date.replace(/-/g, '');
        const t = time ? time.replace(':', '') + '00' : '000000';
        return d + 'T' + t;
    };

    const start = formatGoogleDate(event.date, event.startTime);
    // If no end time, default to 1 hour after start
    const endTime = event.endTime || addHoursToTime(event.startTime, 1) || event.startTime;
    const end = formatGoogleDate(event.date, endTime);

    const location = event.address
        ? `${event.location}, ${event.address}`
        : event.location;

    const details = [
        event.description,
        event.cost ? `Cost: ${event.cost}` : '',
        event.url ? `Register: ${event.url}` : ''
    ].filter(Boolean).join('\n\n');

    const params = new URLSearchParams({
        action: 'TEMPLATE',
        text: event.title,
        dates: `${start}/${end}`,
        location: location,
        details: details
    });

    return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

function toggleCalendarMenu(index) {
    const menu = document.getElementById(`cal-menu-${index}`);
    const isOpen = menu.classList.contains('open');

    // Close all other menus
    document.querySelectorAll('.calendar-menu.open').forEach(m => m.classList.remove('open'));

    if (!isOpen) {
        menu.classList.add('open');
    }
}

// Close menus when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.add-to-cal-wrapper')) {
        document.querySelectorAll('.calendar-menu.open').forEach(m => m.classList.remove('open'));
    }
});

function downloadEventICS(index) {
    const event = filteredEvents[index];
    if (!event) return;

    // Close the menu
    document.querySelectorAll('.calendar-menu.open').forEach(m => m.classList.remove('open'));

    const icsContent = generateICS(event);
    const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    const safeTitle = event.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').substring(0, 50);
    const filename = `${event.date}-${safeTitle}.ics`;

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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

        const eventsHtml = dayEvents.slice(0, 2).map(e => {
            const color = sourceColors[e.source] || '#888';
            const safeTitle = escapeAttr(e.title);
            const safeUrl = escapeAttr(e.url);
            const locationFirst = escapeHtml(e.location.split(' ')[0]);
            return `<div class="cal-event" style="background: ${color}" title="${safeTitle}" onclick="window.open('${safeUrl}', '_blank', 'noopener')">${locationFirst}</div>`;
        }).join('');

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
    viewListBtn.setAttribute('aria-selected', 'true');
    viewCalendarBtn.classList.remove('active');
    viewCalendarBtn.setAttribute('aria-selected', 'false');
    eventsList.classList.remove('hidden');
    eventsCalendar.classList.add('hidden');
});

viewCalendarBtn.addEventListener('click', () => {
    viewCalendarBtn.classList.add('active');
    viewCalendarBtn.setAttribute('aria-selected', 'true');
    viewListBtn.classList.remove('active');
    viewListBtn.setAttribute('aria-selected', 'false');
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
