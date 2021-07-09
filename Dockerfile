FROM python:3.9
COPY ./app .
COPY ./requirements.txt .
RUN python -m pip install -r ./requirements.txt --target .

CMD [ "python", "-u", "products_server.py" ]
EXPOSE 50051