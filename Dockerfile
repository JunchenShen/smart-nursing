FROM python:3.11-bookworm

WORKDIR /project

RUN sed -i 's|http://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://deb.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless \
    procps \
    curl \
    wget \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

ENV PYSPARK_PYTHON=python

COPY requirements.txt .

RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY . .

CMD ["sh", "-c", "export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java)))) && python app/main.py"]
