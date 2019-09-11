FROM digitalmarketplace/base-api:4.5.4

COPY uwsgi.conf /etc/uwsgi.conf
COPY supervisord.conf /etc/supervisord.conf
