!define APP_NAME "Kv2m"
!define APP_VERSION "4.4.0"
!define APP_EXE "Kv2m.exe"
!define INST_DIR "$PROGRAMFILES64\Kv2m"
!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\Kv2m"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "Kv2m-Setup-x64.exe"
InstallDir "${INST_DIR}"
RequestExecutionLevel admin
SetCompressor /SOLID lzma
Unicode True

!include "MUI2.nsh"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Main"
  SetOutPath "${INST_DIR}"
  File "${APP_EXE}"
  CreateDirectory "$SMPROGRAMS\Kv2m"
  CreateShortcut "$SMPROGRAMS\Kv2m\Kv2m.lnk"        "${INST_DIR}\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\Kv2m\Uninstall.lnk"   "${INST_DIR}\Uninstall.exe"
  CreateShortcut "$DESKTOP\Kv2m.lnk"                "${INST_DIR}\${APP_EXE}"
  WriteRegStr   HKLM "${UNINST_KEY}" "DisplayName"     "Kv2m ${APP_VERSION}"
  WriteRegStr   HKLM "${UNINST_KEY}" "DisplayVersion"  "${APP_VERSION}"
  WriteRegStr   HKLM "${UNINST_KEY}" "Publisher"       "KIAN-IRANI"
  WriteRegStr   HKLM "${UNINST_KEY}" "UninstallString" '"${INST_DIR}\Uninstall.exe"'
  WriteRegStr   HKLM "${UNINST_KEY}" "InstallLocation" "${INST_DIR}"
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoRepair"  1
  WriteUninstaller "${INST_DIR}\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "${INST_DIR}\${APP_EXE}"
  Delete "${INST_DIR}\Uninstall.exe"
  RMDir  "${INST_DIR}"
  Delete "$SMPROGRAMS\Kv2m\Kv2m.lnk"
  Delete "$SMPROGRAMS\Kv2m\Uninstall.lnk"
  RMDir  "$SMPROGRAMS\Kv2m"
  Delete "$DESKTOP\Kv2m.lnk"
  DeleteRegKey HKLM "${UNINST_KEY}"
SectionEnd
