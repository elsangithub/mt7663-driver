#!/bin/sh
WIFI_IRQ=$(awk -F: '/ffe03000.mmc/ {gsub(/ /, "", $1); print $1}' /proc/interrupts 2>/dev/null)
if [ -n "$WIFI_IRQ" ] && [ -d "/proc/irq/$WIFI_IRQ" ]; then
    echo 2,3 > /proc/irq/$WIFI_IRQ/smp_affinity_list
fi
if [ -d /sys/class/net/wlan0/queues/rx-0 ]; then
    echo e > /sys/class/net/wlan0/queues/rx-0/rps_cpus
    echo 4096 > /sys/class/net/wlan0/queues/rx-0/rps_flow_cnt 2>/dev/null || true
fi

