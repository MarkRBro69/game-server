@echo off

set services=frontend_service users_service game_service

for %%s in (%services%) do (
    echo directory %%s...
    cd %%s || exit /b 1
    pip freeze > requirements.txt
    cd ..
)

echo end