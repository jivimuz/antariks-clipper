!addplugindir "."
!addplugindir "${NSISDIR}\Plugins\x86-unicode"
!addplugindir "${NSISDIR}\Plugins"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

!macro customInit
  ; ---- Cek free space drive C: minimal 500MB ----
  ${DriveSpace} "C:\" "/D=F /S=M" $0
  ${If} $0 < 500
    MessageBox MB_ICONSTOP "Ruang disk di drive C: kurang dari 500MB. Silakan kosongkan ruang disk sebelum install." /SD IDOK
    Abort
  ${EndIf}

  ; ---- Cek free space di drive tempat $INSTDIR minimal 1GB ----
  ${GetRoot} "$INSTDIR" $1
  ${DriveSpace} "$1" "/D=F /S=M" $0
  ${If} $0 < 1024
    MessageBox MB_ICONSTOP "Not enough disk space (1GB required). Aborting installation." /SD IDOK
    Abort
  ${EndIf}

  ; (opsional) HAPUS dulu check file source tree ini (lihat catatan bawah)
  ; IfFileExists "${INSTALLER_DIR}\..\backend\app.py" +2 0
  ; ...
!macroend


; --- Custom Loading Overlay Page ---
Var LoadingPage
Var LoadingText

Function ShowLoadingPage
  nsDialogs::Create 1018
  Pop $LoadingPage
  ${If} $LoadingPage == 0
    Abort
  ${EndIf}
  nsDialogs::CreateControl /NOUNLOAD Static "" 0x40000000 0 10 100% 30u "Sedang menginstal Antariks Clipper... Mohon tunggu sampai proses selesai."
  nsDialogs::CreateControl /NOUNLOAD Progress "" 0x50000000 0 50 100% 20u ""
  nsDialogs::Show
FunctionEnd

Function HideLoadingPage
  ${If} $LoadingPage <> 0
    nsDialogs::Destroy
    StrCpy $LoadingPage 0
  ${EndIf}
FunctionEnd
!insertmacro MUI_PAGE_INSTFILES

; --- Hook into install process ---
Function .onInstFilesStart
  Call ShowLoadingPage
FunctionEnd

Function .onInstFilesSuccess
  Call HideLoadingPage
FunctionEnd

Function .onInstFilesFailed
  Call HideLoadingPage
FunctionEnd

; Prevent user from closing the loading page
!define MUI_CUSTOMFUNCTION_ABORT "AbortBlocker"
Function AbortBlocker
  ; Do nothing, block abort
FunctionEnd


