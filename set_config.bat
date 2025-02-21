@echo off

set services=frontend_service users_service game_service

for %%s in (%services%) do (
    echo copying to directory %%s...
    copy "config.py" "%%s\config.py"
)

echo end