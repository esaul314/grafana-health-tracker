FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y python3 python3-pip nodejs npm cron

RUN pip3 install --upgrade pip

RUN npm install -g yarn

RUN apt install -y git mc fish vim tig && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/scripts/requirements.txt
RUN pip3 install --no-cache-dir -r /app/scripts/requirements.txt


CMD ["cron", "-f"]
