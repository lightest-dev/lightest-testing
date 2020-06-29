FROM ubuntu:20.04
ARG vcs_ref
ARG build_date
ARG version

LABEL org.label-schema.maintainer="Andrii Vasylyk" \
    org.label-schema.url="https://github.com/lightest-dev/lightest-testing" \
    org.label-schema.name="Lightest testing server" \
    org.label-schema.license="Apache-2.0" \
    org.label-schema.version="$version" \
    org.label-schema.vcs-url="https://github.com/lightest-dev/lightest-testing" \
    org.label-schema.vcs-ref="$vcs_ref" \
    org.label-schema.build-date="$build_date" \
    org.label-schema.schema-version="1.0" \
    org.label-schema.dockerfile="/Dockerfile"

RUN apt update \
    && apt install -y wget python3.8 g++ python3-tempita \
    python3-yaml python3-requests python3-pip \
    python3-protobuf && rm -rf /var/lib/apt/lists/* \
    && pip3 install grpcio
RUN wget https://github.com/sosy-lab/benchexec/releases/download/2.7/benchexec_2.7-1_all.deb && apt install --install-recommends ./benchexec_*.deb && rm benchexec_*.deb
RUN usermod -a -G benchexec root
RUN mkdir lightest
WORKDIR /lightest
COPY dist ./
EXPOSE 10000
CMD ["python3.8", "main.py"]