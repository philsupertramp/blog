---
tags:
 - old-wiki
 - published
title: Dockerfile for ML using Python
description: A template for Dockerfiles using Python for Machine Learning Applications
layout: mylayout.njk
author: Philipp
date: 2023-07-24
---

Dockerizing your strack is probably a thing you will do at one point.
But writing Dockerfiles is relatively repetitive.

Some people rely on OS images published on several repositories, such as [docker-hub](https://hub.docker.com).

But mostly you need some framework, a template, to get started and to build your application container image. 

So without any further ado, take a look at the following examples, one using plane old `pip` the other uses `poetry` ([ref](https://python-poetry.org/docs/))

## PIP

```dockerfile
FROM python:3.12-alpine

RUN apk update \
  && apk add --virtual .build-deps \
      gcc g++ musl-dev libffi-dev linux-headers python3-dev libstdc++ \
      libgfortran gfortran lapack-dev libpng-dev build-base wget openblas-dev \
  && apk add curl bash git coreutils

RUN mkdir -p /code/
WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY . /code/
```

## POETRY
```dockerfile
FROM python:3.12-alpine

ARG GH_TOKEN

ENV PATH=/etc/poetry/bin:${PATH}

RUN apk update \
  && apk add --virtual .build-deps \
      gcc g++ musl-dev libffi-dev linux-headers python3-dev libstdc++ \
      libgfortran gfortran lapack-dev libpng-dev build-base wget openblas-dev \
  && apk add curl bash git openssh openssh-client coreutils

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 - \
  && poetry config virtualenvs.create false

RUN mkdir -p /code/
WORKDIR /code

COPY pyproject.toml /code/
COPY poetry.lock /code/
RUN poetry export --with ml --without-hashes -f requirements.txt --output requirements.txt

RUN pip install -r requirements.txt


COPY . /code/
```
