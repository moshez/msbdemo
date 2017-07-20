FROM python:2.7.13
RUN virtualenv /buildenv
RUN /buildenv/bin/pip install pex wheel
RUN mkdir /wheels
COPY src /src
RUN /buildenv/bin/pip wheel --no-binary :all: twisted /src --wheel-dir /wheels
RUN /buildenv/bin/pex --find-links /wheels --no-index \
                      twisted msbdemo -o /mnt/src/twist.pex -m twisted

FROM python:2.7.13-slim
COPY --from=0 /mnt/src/twist.pex /root
ENTRYPOINT ["/root/twist.pex", "web", "--wsgi", "msbdemo.wsgi.app", \
            "--port", "tcp:80"]
