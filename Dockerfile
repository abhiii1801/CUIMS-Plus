FROM python:3.12-slim

# Install Playwright deps
RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip fonts-liberation libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libxss1 libasound2 libgbm1 libxshmfence1 libxrandr2 libgtk-3-0 \
    libxcomposite1 libxdamage1 libx11-xcb1 libxfixes3 libxext6 libxrender1 libdbus-1-3 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install Playwright + browser deps
RUN playwright install --with-deps

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]