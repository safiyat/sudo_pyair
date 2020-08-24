#!/usr/bin/env bash

set -ex

PACKAGE_NAME=sudo-pyair
PACKAGE_VERSION=0.1

SPEC_FILE_NAME="${PACKAGE_NAME}-${PACKAGE_VERSION}.spec"

export DEBEMAIL=safiyat.reza@ericsson.com
export DEBFULLNAME="Md Safiyat Reza"

SELF=$(readlink -f $0)
PROJECT_ROOT=$(realpath $(dirname ${SELF})/../..)

SPEC_FILE_NAME=sudo-pyair.spec

BUILD_ROOT=$(mktemp -d -t sudo_pyair-rpm-XXXX)
BUILD_DIR=${BUILD_ROOT}/rpmbuild
mkdir -p ${BUILD_ROOT}/
cd ${BUILD_ROOT}

# Create build tree.
mkdir -p rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

# Copy requisites.
cd ${BUILD_DIR}
cp ${PROJECT_ROOT}/packaging/rpm/${SPEC_FILE_NAME} ${BUILD_DIR}/SPECS/
cp ${PROJECT_ROOT}/sudo-pyair/scripts/{approver,approver.py,python_pam_server.py,start_shared_screen} ${BUILD_DIR}/SOURCES/

# Update spec file.
sed -i -e "s#{{OUTPUT_DIR}}#${BUILD_ROOT}#g" "${BUILD_DIR}"/SPECS/${SPEC_FILE_NAME}
sed -i -e "s#{{VERSION}}#${PACKAGE_VERSION}#g" "${BUILD_DIR}"/SPECS/${SPEC_FILE_NAME}
sed -i -e "s#{{BUILD_ROOT}}#${BUILD_DIR}#g" "${BUILD_DIR}"/SPECS/${SPEC_FILE_NAME}

# Build.
cd SPECS
rpmbuild -bb ${SPEC_FILE_NAME}
