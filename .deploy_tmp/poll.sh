#!/bin/bash
sleep 95
journalctl -u geometry-ai --no-pager -n 25 | grep -E "VECTOR|STARTUP|ERROR" | tail -10
