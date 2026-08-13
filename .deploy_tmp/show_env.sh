#!/bin/bash
# 脱敏显示 .env：key名 + 值的前6字符
sed -E 's/^(#.*)$/\1/; s/^([A-Za-z_]+)=(.*)$/\1=\2/' /usr/local/geometry-ai/.env 2>/dev/null | \
awk -F= '{ if (NF>=2 && $1 !~ /^#/) { v=$2; if (length(v)>6) v=substr(v,1,6)"...(len "length($2)")"; print $1"="v } else print }'
