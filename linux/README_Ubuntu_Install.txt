Geometry AI Server - Ubuntu 全自动安装包

version: 1.0.0.90
build: 2026-06-27

安装方式 1: 一键脚本安装（推荐）

  cd linux/
  tar -xzf geometry-ai-server_ubuntu_1.0.0.90_amd64.tar.gz
  cd geometry-ai-server_1.0.0.90_amd64
  sudo bash install.sh

安装方式 2: .deb 包安装（仅限 Ubuntu 22.04+）

  dpkg-deb --build geometry-ai-server_1.0.0.90_amd64
  sudo dpkg -i geometry-ai-server_1.0.0.90_amd64.deb
  sudo apt install -f  # 修复依赖

安装方式 3: 从源码直接运行

  cd geometry-ai-server_1.0.0.90_amd64/usr/local/geometry-ai
  # 编辑 .env 填入 API Key
  python3 server.py

安装后访问:
  http://localhost:5000/admin  - 管理界面
  http://localhost:5000/health - 健康检查

配置文件: /usr/local/geometry-ai/.env

常见命令:
  sudo systemctl status geometry-ai
  sudo journalctl -u geometry-ai -f
  sudo systemctl restart geometry-ai
