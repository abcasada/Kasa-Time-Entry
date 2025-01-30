cd "C:\ProgramFiles\Kasa-Time-Entry"
git remote update
if not "%errorlevel%"=="0" exit /b %errorlevel%
setlocal EnableDelayedExpansion
set commitMessage=
for /f %%i in ('git rev-parse --abbrev-ref HEAD') do (set /p commitMessage=<nul & git log --oneline ..origin/%%i)
if not "!commitMessage!"=="" (
    git pull origin %%i
)
endlocal

python "C:\ProgramFiles\Kasa-Time-Entry\src\main.py"
