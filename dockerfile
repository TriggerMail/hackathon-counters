# Sample Python 2.7 gunicorn web app Dockerfile
FROM python:2.7.14-slim-stretch
LABEL maintainer="awesomeness"

EXPOSE 8080

# This argument gives us the URL to access our private pypi repository.
# this is usually set by bluecore activate as $PIP_EXTRA_INDEX_URL
ARG PIP_EXTRA_INDEX_URL

WORKDIR /app
COPY . /app/

# disable pip cache dir: it should not exist, and there is no point adding entries to it
RUN pip install --no-cache-dir -r /app/requirements.txt

# A minimal base image that defaults to a non-root user
FROM gcr.io/distroless/base-debian10:nonroot
EXPOSE 8080

CMD ["python", "app/pubsub.py"]


