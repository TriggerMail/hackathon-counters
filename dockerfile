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

# Disable keepalive: By default gthread workers keep connections around for 2 seconds
# this causes a race with the Google Cloud Load Balancer that causes 502 errors with
# cause backend_connection_closed_before_data_sent_to_client error. Verified using script from:
# https://blog.percy.io/tuning-nginx-behind-google-cloud-platform-http-s-load-balancer-305982ddb340
CMD ["gunicorn", "/app:app", "--worker-class=gthread", "--keep-alive=0",\
  "--bind=:8080", "--threads=8"]
