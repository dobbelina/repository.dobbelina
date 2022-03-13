;@Ahk2Exe-SetCopyright    Dobbelina
;@Ahk2Exe-SetDescription  VLC Parser
;@Ahk2Exe-SetFileVersion   1.0.0.0
;@Ahk2Exe-SetProductName   VLCParser.exe
;@Ahk2Exe-SetProductVersion   1.0.0.0

#NoEnv
#SingleInstance force
SetWorkingDir %A_ScriptDir%

Incoming0 := A_Args[1]
Incoming := UrlDecode(Incoming0)
Clipboard := Incoming


RegExMatch(Incoming, "^[a-zA-Z]{1,5}:.*?(?=[|]|$)", Link0)
Link:= chr(34) . Link0 . chr(34)
RegExMatch(Incoming, "(?i)(?<=user-agent=)(.*?)(?=&|$)", Uagent0)
if (Uagent0)
Uagent:= "--http-user-agent=" . chr(34) . Uagent0 . chr(34)
RegExMatch(Incoming, "(?i)(?<=Referer=)(.*?)(?=&|$)", Referer0)
if (Referer0)
Referer:= "--http-referrer=" . chr(34) . Referer0 . chr(34)



Run, vlc.exe %Uagent% %Referer% %Link% 

ExitApp

UrlDecode(str) {
   Loop
   If RegExMatch(str, "i)(?<=%)[\da-f]{1,2}", hex)
   str := StrReplace(str, "%" . hex, Chr("0x" . hex))
   Else Break
   Return, str
}

