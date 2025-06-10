@echo off
for /L %%i in (1,1,1000) do (
    curl http://127.0.0.1:5000 >nul
)
