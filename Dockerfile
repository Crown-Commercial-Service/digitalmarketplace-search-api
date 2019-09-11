FROM digitalmarketplace/base-api:4.5.4

RUN /usr/local/bin/pip3 install -U --no-cache-dir uwsgi==2.0.18
COPY uwsgi.conf /etc/uwsgi.conf
COPY supervisord.conf /etc/supervisord.conf
