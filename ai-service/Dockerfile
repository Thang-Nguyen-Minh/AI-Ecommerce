# Kế thừa từ AI base image
FROM ecom-ai-base:latest

WORKDIR /app

# Chỉ copy code
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]