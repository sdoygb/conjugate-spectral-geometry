============================================================
Geometry AI Server - macOS 安装说明
============================================================

【全自动安装】
  1. 双击 install_mac.sh（或在终端执行: bash install_mac.sh）
  2. 脚本会自动：检查 Python、安装依赖、配置 API Key、注册开机自启
  3. 首次运行需要输入 API Key（在 https://platform.deepseek.com 获取）

【手动安装】
  如果全自动安装失败，请按以下步骤操作：

一、环境要求
------------
- macOS 12+ (Monterey 或更高)
- Python 3.9+ (系统自带或 Homebrew 安装)

二、安装依赖
------------
  cd app
  pip3 install -r requirements.txt

三、配置
--------
  复制 .env.example 为 .env，填入 API Key

四、启动
--------
  python3 server.py

五、开机自启（可选）
------------------
  运行 install_mac.sh 会自动配置 launchd 服务
  或手动: launchctl load ~/Library/LaunchAgents/com.geometryai.server.plist

【管理界面】
  http://localhost:5000/admin

【停止服务】
  launchctl unload ~/Library/LaunchAgents/com.geometryai.server.plist

【卸载】
  1. launchctl unload ~/Library/LaunchAgents/com.geometryai.server.plist
  2. rm ~/Library/LaunchAgents/com.geometryai.server.plist
  3. 删除安装目录
