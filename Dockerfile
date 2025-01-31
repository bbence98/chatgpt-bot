FROM python:3.12

WORKDIR /chatgpt-bot

COPY . .

VOLUME [ "/chatgpt-data" ]

RUN apt-get update && apt-get install -y unzip curl
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
RUN cd /tmp
RUN unzip /tmp/awscliv2.zip
RUN ./aws/install
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

EXPOSE 8700

CMD [ "python3", "main.py" ]
