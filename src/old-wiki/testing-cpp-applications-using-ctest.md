---
tags:
 - old-wiki
 - published
title: Testing C++ applications using ctest
description: Testing C++ applications using ctest
layout: mylayout.njk
author: Philipp
date: 2022-09-25
---

### Requirements
- Docker
- a C++ application

`Dockerfile` for gcc, cmake build system  

 	FROM alpine:3.13

	RUN apk add build-base gcc abuild binutils binutils-doc gcc-doc
	RUN apk add --no-cache make cmake
	
	ENV CMAKE_CXX_COMPILER=gcc

The image can be found at [philsupertramp/cpp-test](https://hub.docker.com/r/philsupertramp/cpp-test).

Mount your project-directory into the container and set the working directory to it.  
For convenience I'll execute the command within my project directory

 	docker run --rm -v ${PWD}:/usr/app -w /usr/app philsupertramp/cpp-test:latest make test
