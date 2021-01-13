FROM python:3.9-alpine

RUN pip install --no-cache-dir -r requirements.txt

CMD["python", "-u", "__init__.py"]
