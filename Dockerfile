FROM python:3.9

COPY __init__.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD["python", "-u", "__init__.py"]
