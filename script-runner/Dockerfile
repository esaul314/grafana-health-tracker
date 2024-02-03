FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y python3 python3-pip libcairo2-dev libjpeg-dev libgif-dev pkg-config nodejs npm cron

RUN pip3 install --upgrade pip

RUN npm install -g yarn

RUN apt install -y git mc fish vim tig && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/scripts/requirements.txt
RUN pip3 install --no-cache-dir -r /app/scripts/requirements.txt

ADD crontab /app/scripts/crontab

RUN crontab -u root /app/scripts/crontab

CMD ["cron", "-f"]
