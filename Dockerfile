FROM centos:latest

RUN yum install -y epel-release \
  # Install deps
  && yum install -y \
    git \
    python-devel \
    python-pip \
    rpm-build \

  # Install Python deps
  && pip install tox \

  # Cleanup
  && yum clean all \
  && rm -rf /tmp/* \
  && rm -rf /var/tmp/*
