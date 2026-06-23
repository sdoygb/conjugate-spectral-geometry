============================================================
Geometry AI Server - Windows 安装说明
============================================================

【全自动安装】
  双击 install.bat，等待安装完成即可。
  脚本会自动：下载 Python、安装依赖、下载 NSSM、配置服务。
  首次运行需要输入 API Key（在 https://platform.deepseek.com 获取）。

【手动安装】
  如果全自动安装失败，请按以下步骤操作：

一、前置准备
------------
1. 准备 Windows 嵌入式 Python (Embedded Python)
   - 下载地址: https://www.python.org/downloads/windows/
   - 选择 "Windows embeddable package (64-bit)"
   - 解压后将全部内容放入 python/ 目录

2. 安装 Python 依赖
   - 在 Windows 上打开命令提示符
   - cd python
   - python.exe -m pip install --target=. -r ..\app\requirements.txt

3. 下载 NSSM (Non-Sucking Service Manager)
   - 下载地址: https://nssm.cc/download
   - 将 nssm.exe 放入 build/ 目录

二、编译安装程序
----------------
1. 安装 Inno Setup 6.x
   - 下载地址: https://jrsoftware.org/isdl.php

2. 将整个 build/ 目录和 windows/installer.iss 复制到 Windows 机器

3. 用 Inno Setup 打开 installer.iss，点击编译 (Build)

4. 编译完成后，在 installer_output/ 目录找到安装程序 .exe

三、文件结构
------------
build/
  python/          - Windows 嵌入式 Python 运行时（需手动放入）
  app/             - 应用程序文件
    server.py      - 主服务入口
    config.py      - 配置模块
    knowledge.py   - 知识库模块
    models.py      - 数据模型
    prompts.py     - 提示词系统
    tools.py       - 工具函数
    stream.py      - 流式输出
    admin_routes.py - 管理界面路由
    auto_teach.py  - 自动教学
    start.py       - 启动辅助
    articles/      - 知识库文章
    chroma_db/     - 向量数据库
    templates/     - HTML 模板
    requirements.txt - Python 依赖列表
    .env.example   - 环境变量示例
  nssm.exe         - Windows 服务管理器（需手动放入）
  install_service.bat  - 服务注册脚本
  uninstall_service.bat - 服务卸载脚本
  start.bat        - 手动启动脚本

四、安装后配置
--------------
安装程序会引导你输入 API Key 和 Base URL。
配置文件保存在安装目录的 app/.env 中。

管理界面: http://localhost:5000/admin

============================================================
