FROM python:3.7

WORKDIR /hello-python
COPY ./ ./
RUN pip install -r app/requirements.txt

EXPOSE 5000
CMD ["python", "app/main.py"]
