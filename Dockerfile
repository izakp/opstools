FROM cgr.dev/chainguard/python:latest-dev

USER root
RUN apk --no-cache add \
  curl \
  git \
  make

RUN adduser --disabled-password --gecos '' deploy
RUN mkdir -p /src
RUN chown deploy:deploy /src

RUN pip --no-cache-dir install poetry
RUN pip --no-cache-dir install awscli --upgrade

ARG terraform_version=0.12.31
ARG kubectl_version=1.19.16

RUN curl https://releases.hashicorp.com/terraform/${terraform_version}/terraform_${terraform_version}_linux_amd64.zip \
  -o /tmp/terraform_${terraform_version}_linux_amd64.zip \
  && unzip -d /tmp /tmp/terraform_${terraform_version}_linux_amd64.zip \
  && chmod +x /tmp/terraform \
  && mv /tmp/terraform /usr/bin/terraform

RUN curl https://storage.googleapis.com/kubernetes-release/release/v${kubectl_version}/bin/linux/amd64/kubectl -o /tmp/kubectl \
  && chmod 755 /tmp/kubectl \
  && mv /tmp/kubectl /usr/bin/kubectl

WORKDIR /src

COPY pyproject.toml poetry.lock /src/
RUN poetry config virtualenvs.create false \
  && poetry install --without dev

USER deploy
ENV USER deploy
ENV HOME /home/deploy

COPY . /src

# Uncomment to debug
# ENTRYPOINT ["/bin/sh"]
CMD ["python"]
