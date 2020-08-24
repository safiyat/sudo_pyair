#!/usr/bin/env bash

set -x

PACKAGE_NAME=sudo-pyair
PACKAGE_VERSION=0.1
DEBIAN_VERSION=1

export DEBEMAIL=safiyat.reza@ericsson.com
export DEBFULLNAME="Md Safiyat Reza"

SELF=$(readlink -f $0)
PROJECT_ROOT=$(realpath $(dirname ${SELF})/../..)

BUILD_DIR=$(mktemp -d -t sudo_pyair-deb-XXXX)/${PACKAGE_NAME}-${PACKAGE_VERSION}
mkdir -p ${BUILD_DIR}/

# Data layout.
mkdir -p ${BUILD_DIR}/${PACKAGE_NAME}/{opt,usr/local/bin}

# Copy data files.
cp ${PROJECT_ROOT}/sudo-pyair/scripts/approver.py ${PROJECT_ROOT}/sudo-pyair/scripts/python_pam_server.py ${BUILD_DIR}/${PACKAGE_NAME}/opt/
chmod 0644 ${BUILD_DIR}/${PACKAGE_NAME}/opt/*
cp ${PROJECT_ROOT}/sudo-pyair/scripts/approver ${PROJECT_ROOT}/sudo-pyair/scripts/start_shared_screen ${BUILD_DIR}/${PACKAGE_NAME}/usr/local/bin
chmod 0755 ${BUILD_DIR}/${PACKAGE_NAME}/usr/local/bin/*

# Build the layout.
cd ${BUILD_DIR}
mkdir debian

# Changelog.
dch --create --empty -v ${PACKAGE_VERSION}-${DEBIAN_VERSION} --package ${PACKAGE_NAME}
dch --append "Created sudo-pypair."  # Add more if necessary.
dch --distribution bionic --release ""

cp ${PROJECT_ROOT}/packaging/deb/debian/{compat,control,postinst,rules} debian/

dpkg-buildpackage --pre-clean --unsigned-changes --unsigned-source
