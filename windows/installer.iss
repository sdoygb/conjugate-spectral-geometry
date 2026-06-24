; ============================================================
; Geometry AI Server - Inno Setup 安装脚本
; 使用 Inno Setup 6.x 编译
; ============================================================

#define MyAppName "Geometry AI Server"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Geometry AI"
#define MyAppExeName "server.py"
#define MyAppURL ""
#define MyAppDesc "几何论 AI 学习平台服务"

[Setup]
; 基本信息
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\GeometryAI
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; 输出设置
OutputDir=installer_output
OutputBaseFilename=GeometryAI-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
; 安装界面
WizardStyle=modern
WizardSizePercent=120
; 权限
PrivilegesRequired=admin
; 其他
UninstallDisplayIcon={app}\nssm.exe
UninstallDisplayName={#MyAppName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; 语言
ShowLanguageDialog=no

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
; 安装完成后启动服务
Name: "installservice"; Description: "注册并启动 Windows 服务（开机自动运行）"; Flags: checkedonce
; 安装完成后打开管理界面
Name: "openadmin"; Description: "安装完成后打开管理界面"; Flags: checkedonce
; 创建桌面快捷方式
Name: "desktopicon"; Description: "创建桌面快捷方式"; Flags: checkedonce

[Files]
; Python 环境
Source: "build\python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs; AfterInstall: SetPythonPath
; 应用程序文件
Source: "build\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs
; NSSM 服务管理器
Source: "build\nssm.exe"; DestDir: "{app}"; Flags: ignoreversion
; 批处理脚本
Source: "windows\*.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; 开始菜单快捷方式
Name: "{group}\{#MyAppName}"; Filename: "http://localhost:5000/admin"
Name: "{group}\启动服务（调试模式）"; Filename: "{app}\start.bat"; WorkingDir: "{app}"
Name: "{group}\卸载服务"; Filename: "{app}\uninstall_service.bat"; WorkingDir: "{app}"
; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "http://localhost:5000/admin"; Tasks: desktopicon

[Run]
; 安装完成后执行的操作
Filename: "{app}\install_service.bat"; Parameters: ""; Flags: runhidden; Tasks: installservice; StatusMsg: "正在注册 Windows 服务..."
Filename: "http://localhost:5000/admin"; Flags: shellexec nowait postinstall; Tasks: openadmin; Description: "打开管理界面"

[UninstallRun]
; 卸载前停止并移除服务
Filename: "{app}\uninstall_service.bat"; Parameters: ""; Flags: runhidden; RunOnceId: "UninstallService"

[UninstallDelete]
; 卸载时清理日志文件
Type: filesandordirs; Name: "{app}\logs"

[Code]
// ============================================================
// 自定义向导页变量
// ============================================================
var
  APIKeyPage: TInputQueryWizardPage;
  BaseURLPage: TInputQueryWizardPage;

// ============================================================
// 初始化向导页
// ============================================================
procedure InitializeWizard;
begin
  // --- API Key 输入页 ---
  APIKeyPage := CreateInputQueryPage(wpSelectDir,
    '配置 API Key',
    '请输入您的 AI 模型 API Key',
    '该 Key 将保存到配置文件中，用于调用 AI 模型接口。');

  APIKeyPage.Add('API Key:', False);
  APIKeyPage.Values[0] := '';

  // --- Base URL 输入页 ---
  BaseURLPage := CreateInputQueryPage(APIKeyPage.ID,
    '配置 API Base URL',
    '请输入 AI 模型的 Base URL',
    '留空则使用默认地址（https://api.openai.com/v1）。');

  BaseURLPage.Add('Base URL:', False);
  BaseURLPage.Values[0] := 'https://api.openai.com/v1';
end;

// ============================================================
// 安装前检查：检测是否已安装旧版本
// ============================================================
function InitializeSetup(): Boolean;
var
  OldAppDir: String;
  ResultCode: Integer;
begin
  Result := True;

  // 检查注册表中是否已有安装记录
  if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}_is1', 'InstallLocation', OldAppDir) then
  begin
    // 检测到已安装版本，提示用户
    if MsgBox('检测到已安装的 Geometry AI Server，版本将覆盖更新。' + #13#10 +
              '现有的 .env 配置文件和 chroma_db 数据库将被保留。' + #13#10#13#10 +
              '是否继续安装？',
              mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;

    // 停止旧版本服务
    if FileExists(OldAppDir + '\nssm.exe') then
    begin
      Exec(OldAppDir + '\nssm.exe', 'stop GeometryAI', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;

// ============================================================
// 安装步骤后处理：生成 .env 配置文件
// ============================================================
procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvFilePath: String;
  EnvContent: String;
  LogsDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    // 创建日志目录
    LogsDir := ExpandConstant('{app}\logs');
    if not DirExists(LogsDir) then
      ForceDirectories(LogsDir);

    // 生成 .env 配置文件（仅在不存在时创建，保留用户配置）
    EnvFilePath := ExpandConstant('{app}\app\.env');
    if not FileExists(EnvFilePath) then
    begin
      EnvContent := '# Geometry AI Server 配置文件' + #13#10;
      EnvContent := EnvContent + '# 此文件由安装程序自动生成' + #13#10;
      EnvContent := EnvContent + 'API_KEY=' + APIKeyPage.Values[0] + #13#10;
      EnvContent := EnvContent + 'BASE_URL=' + BaseURLPage.Values[0] + #13#10;
      EnvContent := EnvContent + 'HOST=0.0.0.0' + #13#10;
      EnvContent := EnvContent + 'PORT=5000' + #13#10;
      SaveStringToFile(EnvFilePath, EnvContent, False);
    end;
  end;
end;

// ============================================================
// 设置 Python 路径（Files 段 AfterInstall 回调）
// ============================================================
procedure SetPythonPath();
var
  PythonPath: String;
  ResultCode: Integer;
begin
  // 将 app 目录添加到 PYTHONPATH，确保模块导入正常
  PythonPath := ExpandConstant('{app}\app');
  // 写入环境变量（仅对当前安装会话有效，服务启动时由 install_service.bat 设置 AppDirectory）
end;

// ============================================================
// 安装完成后：添加防火墙规则
// ============================================================
procedure CurPageChanged(CurPageID: Integer);
var
  ResultCode: Integer;
begin
  if CurPageID = wpFinished then
  begin
    // 添加防火墙入站规则，允许 5000 端口
    Exec('netsh', 'advfirewall firewall add rule name="Geometry AI Server" dir=in action=allow protocol=tcp localport=5000 profile=any',
         '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
