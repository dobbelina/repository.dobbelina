;@Ahk2Exe-SetCopyright    Dobbelina
;@Ahk2Exe-SetDescription  Kodi Flaresolverr Autostart
;@Ahk2Exe-SetFileVersion   1.0.0.0
;@Ahk2Exe-SetProductName   FlareKodi.exe
;@Ahk2Exe-SetProductVersion   1.0.0.0

#NoEnv
#Persistent
#SingleInstance ignore
SetWorkingDir %A_ScriptDir%

SetTimer, CheckProcesses, 10000 ; Run CheckProcesses every 10 seconds

CheckProcesses:
; Check if Kodi is running
If ProcessExist("kodi.exe") {
    ; Check if Flaresolverr is also running
    If ProcessExist("flaresolverr.exe") {
        ; Both Kodi and Flaresolverr are running, do nothing
    } else {
        ; Kodi is running but Flaresolverr is not, so start Flaresolverr
        Run, flaresolverr.exe,,Hide
    }
} else {
    ; Kodi is not running, check if Flaresolverr is running
    If ProcessExist("flaresolverr.exe") {
        ; Flaresolverr is running but Kodi is not, so close Flaresolverr
        Process, Close, flaresolverr.exe
    }
}

ProcessExist(exeName) {
    Process, Exist, %exeName%
    return ErrorLevel
}
