@echo off
REM Display available commands

echo.
echo ========================================
echo ecom-final — Available Commands
echo ========================================
echo.
echo Batch Files:
echo   build-base.bat    Build base images (run once)
echo   build.bat         Build service images (fast)
echo   up.bat            Start system
echo   down.bat          Stop system
echo   logs.bat          View all logs
echo   ps.bat            Check container status
echo   clean.bat         Remove containers/volumes
echo   rebuild.bat       Full rebuild
echo.
echo Service Logs:
echo   logs-user.bat     View user-service logs
echo   logs-product.bat  View product-service logs
echo   logs-order.bat    View order-service logs
echo   logs-ai.bat       View AI service logs
echo.
echo Other:
echo   migrate.bat       Run database migrations
echo   help.bat          Show this help
echo.
