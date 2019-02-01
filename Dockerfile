FROM docker-hub.trobz.com:443/dev/trobz-odoo-project:12.0

ADD config/apt-requirements.txt /

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends $(grep -v '^#' apt-requirements.txt)

ADD config/pip-requirements.txt /

RUN pip install --no-cache-dir -r pip-requirements.txt

RUN rm apt-requirements.txt pip-requirements.txt