from python:3.8.0-slim
RUN pip install --upgrade pip
COPY ./requirement.txt /app/requirement.txt
WORKDIR /app
RUN pip install -r requirement.txt
COPY . /app
CMD ["python", "./Slack-bot.py"]
