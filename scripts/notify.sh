#!/bin/bash
#
# macOS notification helper for RVA Figure Drawing Calendar scripts.
# Uses terminal-notifier for clickable notifications.
#
# Usage: source notify.sh
#        notify "Title" "Message" "/path/to/logfile"
#        notify_error "Title" "Message" "/path/to/logfile"
#

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

notify() {
    local title="$1"
    local message="$2"
    local log_file="$3"
    local open_arg=()
    if [ -n "$log_file" ]; then
        open_arg=(-open "file://$log_file")
    fi
    terminal-notifier \
        -title "$title" \
        -message "$message" \
        -group "rva-figure-drawing" \
        "${open_arg[@]}" 2>/dev/null || true
}

notify_error() {
    local title="$1"
    local message="$2"
    local log_file="$3"
    local open_arg=()
    if [ -n "$log_file" ]; then
        open_arg=(-open "file://$log_file")
    fi
    terminal-notifier \
        -title "$title" \
        -message "$message" \
        -group "rva-figure-drawing" \
        -sound Basso \
        "${open_arg[@]}" 2>/dev/null || true
}
