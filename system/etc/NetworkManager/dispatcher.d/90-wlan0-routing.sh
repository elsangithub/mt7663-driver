#!/bin/bash
IFACE="$1"
ACTION="$2"

if [ "$IFACE" = "wlan0" ]; then
    if [ "$ACTION" = "up" ]; then
        WLAN_IP=$(ip -4 -o addr show dev wlan0 | awk '{print $4}' | cut -d/ -f1)
        WLAN_GW=$(ip route show dev wlan0 | grep default | awk '{print $3}')
        WLAN_SUBNET=$(ip route show dev wlan0 | grep 'proto kernel' | awk '{print $1}')
        
        if [ -n "$WLAN_IP" ] && [ -n "$WLAN_GW" ]; then
            ip route replace default via "$WLAN_GW" dev wlan0 table 200
            [ -n "$WLAN_SUBNET" ] && ip route replace "$WLAN_SUBNET" dev wlan0 proto kernel scope link src "$WLAN_IP" table 200
            ip rule del from "$WLAN_IP" lookup 200 2>/dev/null || true
            ip rule add from "$WLAN_IP" lookup 200 priority 100
        fi
    elif [ "$ACTION" = "down" ]; then
        ip rule del lookup 200 2>/dev/null || true
        ip route flush table 200 2>/dev/null || true
    fi
elif [ "$IFACE" = "eth0" ] && [ "$ACTION" = "down" ]; then
    # When LAN cable is disconnected: if wlan0 is on 5GHz, auto-fallback Hotspot to 2.4GHz
    if [ -x "/usr/sbin/mt7663-hotspot" ]; then
        /usr/sbin/mt7663-hotspot auto-fallback-2g >/dev/null 2>&1 || true
    fi
fi
