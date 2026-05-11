FROM listmonk/listmonk:v6.1.0

COPY entrypoint.sh /entrypoint.sh
COPY config/config.toml /listmonk/config.toml

RUN chmod +x /entrypoint.sh

EXPOSE 9000

ENTRYPOINT ["/entrypoint.sh"]
