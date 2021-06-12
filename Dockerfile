FROM python:3.9
COPY ./app .
COPY ./requirements.txt .
RUN python -m pip install -r ./requirements.txt --target .

# CMD python products_server.py --email testmail1244545453@gmail.com --password Password123_
CMD [ "python", "-u", "products_server.py", "--email", "testmail1244545453@gmail.com", "--password", "Password123_" ]
EXPOSE 50051