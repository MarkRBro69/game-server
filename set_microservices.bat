@echo off

set services=frontend_service users_service game_service

for %%s in (%services%) do (
    echo copying to directory %%s...
    copy "microservices" "%%s\%%s\microservices\"
)

echo end