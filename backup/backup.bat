@echo off
:: ./backup/backup.bat
:: 复制到备份目录，并重命名为当前日期时间(db_name YY.MM.DD.db)
:: 创建目标文件夹
mkdir "..\backup\automata%date:~2,2%.%date:~5,2%.%date:~8,2%"
copy  ..\lookup_patch.db  "..\backup\automata%date:~2,2%.%date:~5,2%.%date:~8,2%\lookup_patch %date:~2,2%.%date:~5,2%.%date:~8,2%.db"
copy  ..\puzzle.db  "..\backup\automata%date:~2,2%.%date:~5,2%.%date:~8,2%\puzzle %date:~2,2%.%date:~5,2%.%date:~8,2%.db"
copy  ..\stargazer.db  "..\backup\automata%date:~2,2%.%date:~5,2%.%date:~8,2%\stargazer %date:~2,2%.%date:~5,2%.%date:~8,2%.db"
copy  ..\yzdd.db  "..\backup\automata%date:~2,2%.%date:~5,2%.%date:~8,2%\yzdd %date:~2,2%.%date:~5,2%.%date:~8,2%.db"
copy  ..\config.json  "..\backup\automata%date:~2,2%.%date:~5,2%.%date:~8,2%\config %date:~2,2%.%date:~5,2%.%date:~8,2%.json"
copy  ..\user_cookie.json  "..\backup\automata%date:~2,2%.%date:~5,2%.%date:~8,2%\user_cookie %date:~2,2%.%date:~5,2%.%date:~8,2%.json"
::copy  ..\blacklist.db  "..\backup\automata%date:~2,2%.%date:~5,2%.%date:~8,2%\blacklist %date:~2,2%.%date:~5,2%.%date:~8,2%.db"
::copy  ..\blacklist.xlsx  "..\backup\automata%date:~2,2%.%date:~5,2%.%date:~8,2%\blacklist %date:~2,2%.%date:~5,2%.%date:~8,2%.xlsx"


pause

