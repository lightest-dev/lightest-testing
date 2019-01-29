FROM ubuntu:18.10
ARG vcs_ref
ARG build_date

LABEL org.label-schema.maintainer="Andrii Vasylyk" \
      org.label-schema.url="https://github.com/lightest-dev/lightest-testing" \
      org.label-schema.name="Lightest testing server" \
      org.label-schema.license="Apache-2.0" \
      org.label-schema.version="$VERSION" \
      org.label-schema.vcs-url="https://github.com/lightest-dev/lightest-testing" \
      org.label-schema.vcs-ref="$vcs_ref" \
      org.label-schema.build-date="$build_date" \
      org.label-schema.schema-version="1.0" \
      org.label-schema.dockerfile="/Dockerfile"

RUN apt update \
&& apt install -y wget python3.7 build-essential g++ python3-tempita \
python3-yaml python3-requests\
&& rm -rf /var/lib/apt/lists/* 
RUN wget https://github.com/sosy-lab/benchexec/releases/download/1.17/benchexec_1.17-1_all.deb && dpkg -i benchexec_*.deb && rm benchexec_*.deb
RUN usermod -a -G benchexec root
RUN mkdir lightest
WORKDIR /lightest
COPY dist ./
EXPOSE 10000
CMD ["python3.7", "-m", "benchexec.check_cgroups"]
CMD ["python3.7", "main.py"]