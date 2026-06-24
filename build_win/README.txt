============================================================
Geometry AI Server - Windows 安装说明
============================================================

【全自动安装】
  1. 解压 GeometryAI-Win-Build.zip 到任意目录
  2. 双击 install_win.bat
  3. 脚本会自动：检查 Python、安装依赖、配置 API Key、注册开机自启
  4. 首次运行需要输入 API Key（在 https://platform.deepseek.com 获取）

【手动安装】
  如果全自动安装失败，请按以下步骤操作：

一、环境要求
------------
- Windows 10/11
- Python 3.11+（安装时勾选 "Add Python to PATH"）

二、安装依赖
------------
  cd app
  pip install -r requirements.txt

三、配置
--------
  复制 .env.example 为 .env，填入 API Key

四、启动
--------
  python server.py

五、开机自启（可选）
------------------
  运行 install_win.bat 会自动配置
  或手动将 start_server.bat 放到启动文件夹：
  Win+R 输入 shell:startup

【管理界面】
  http://localhost:5000/admin

【聊天界面】
  http://localhost:8080

  首次打开需要：
  1. 创建管理员账号（注册）
  2. 登录后，点击左下角头像 → Settings（设置）
  3. 左侧选 Connections（连接）
  4. 确认 OpenAI API 连接：
     - URL: http://localhost:5000/v1
     - Key: 随便填（如 sk-123）
  5. 回到聊天页面，点左上角模型下拉框
  6. 选择 deepseek-v4-pro（主力模型）或 deepseek-v4-flash（快速模型）
  7. 开始聊天！

【停止服务】
  双击 uninstall_win.bat

【卸载】
  1. 双击 uninstall_win.bat
  2. 删除安装目录
