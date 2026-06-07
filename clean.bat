@echo off
REM Clean up - remove containers and volumes

docker-compose down -v --remove-orphans
echo Cleaned up containers and volumes.
