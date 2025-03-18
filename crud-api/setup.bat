@echo off
echo Setting up the PostgreSQL database...

:: Load environment variables from .env file
for /f "tokens=1,2 delims==" %%i in (./config/.env) do set %%i=%%j

:: Run the SQL script to initialize the database
psql -U %DB_USER% -h %DB_HOST% -p %DB_PORT% -f .\crud-api\init.sql

echo Database setup complete!
pause

