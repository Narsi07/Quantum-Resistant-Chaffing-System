@echo off
REM PostgreSQL Database Setup Script for Quantum-Resistant Chaffing System

echo ========================================
echo PostgreSQL Database Setup
echo ========================================
echo.

REM Set PostgreSQL bin path
set PSQL_PATH="C:\Program Files\PostgreSQL\18\bin\psql.exe"

echo PostgreSQL Version:
%PSQL_PATH% --version
echo.

echo ========================================
echo Creating Database: qr_chaffing
echo ========================================
echo.
echo You will be prompted for the PostgreSQL password.
echo (This is the password you set during PostgreSQL installation)
echo.

REM Create database
%PSQL_PATH% -U postgres -c "CREATE DATABASE qr_chaffing;"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Database created successfully.
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Copy backend\.env.example to backend\.env
    echo 2. Edit backend\.env and set your PostgreSQL password
    echo 3. Run: cd backend
    echo 4. Run: uvicorn app.main:app --reload
    echo.
) else (
    echo.
    echo ========================================
    echo Database may already exist or error occurred.
    echo ========================================
    echo.
    echo To check existing databases, run:
    echo %PSQL_PATH% -U postgres -l
    echo.
)

echo Press any key to exit...
pause >nul
