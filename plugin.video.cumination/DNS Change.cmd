ECHO OFF
set DNS1=8.8.8.8
set DNS2=8.8.4.4
set INTERFACE=Ethernet
CLS
:MENU
ECHO.
ECHO ...............................................
ECHO PRESS 1 OR 2 to select your task, or 3 to EXIT.
ECHO ...............................................
ECHO.
ECHO 1 - Set Static ip 
ECHO 2 - Obtain DNS Automatically
ECHO 3 - EXIT
ECHO.
SET /P M=Type 1, 2, 3, or 4 then press ENTER:
IF %M%==1 GOTO NOTE
IF %M%==2 GOTO CALC
IF %M%==3 GOTO EOF
:NOTE
netsh int ipv4 set dns name="%INTERFACE%" static %DNS1% primary validate=no
netsh int ipv4 add dns name="%INTERFACE%" %DNS2% index=2

ipconfig /flushdns
GOTO MENU
:CALC
netsh interface ipv4 set dnsservers "%INTERFACE%" dhcp
ipconfig /flushdns
GOTO MENU
