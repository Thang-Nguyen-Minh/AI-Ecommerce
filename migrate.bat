@echo off
REM Run migrations for all services

echo.
echo Running migrations...
echo.

docker-compose exec user-service     python manage.py migrate
docker-compose exec product-service  python manage.py migrate
docker-compose exec cart-service     python manage.py migrate
docker-compose exec order-service    python manage.py migrate
docker-compose exec payment-service  python manage.py migrate
docker-compose exec shipping-service python manage.py migrate

echo.
echo Migrations complete!
echo.
