#!/bin/bash
echo "=== 服务器网络配置 ==="
ip addr show | grep -E "^[0-9]+:|inet " | head -15
echo ""
echo "=== 默认路由 ==="
ip route | head -5
echo ""
echo "=== ping 网关 ==="
GW=$(ip route | grep default | awk '{print $3}')
echo "网关: $GW"
ping -c 2 -W 2 $GW 2>&1 | tail -2
echo ""
echo "=== ARP 邻居表（局域网设备） ==="
ip neigh | head -25
echo ""
echo "=== 服务器监听端口 ==="
ss -tlnp 2>/dev/null | head -25
