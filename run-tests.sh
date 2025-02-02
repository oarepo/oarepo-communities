#!/bin/bash
set -e

MODEL="thesis"
CODE_TEST_DIR="tests"
BUILD_TEST_DIR="tests"

BUILDER_VENV=".venv-builder"
TESTS_VENV=".venv-tests"
export PYTHONWARNINGS="ignore"
export PIP_EXTRA_INDEX_URL=https://gitlab.cesnet.cz/api/v4/projects/1408/packages/pypi/simple
export UV_EXTRA_INDEX_URL=https://gitlab.cesnet.cz/api/v4/projects/1408/packages/pypi/simple

OAREPO_VERSION=${OAREPO_VERSION:-12}
PYTHON=${PYTHON:-python3}

if test -d $BUILDER_VENV ; then
	rm -rf $BUILDER_VENV
fi
${PYTHON} -m venv $BUILDER_VENV
. $BUILDER_VENV/bin/activate
pip install -U setuptools pip wheel
pip install oarepo-model-builder oarepo-model-builder-requests \
            oarepo-model-builder-drafts \
            oarepo-model-builder-communities \
            oarepo-model-builder-workflows


curl -L -o forked_install.sh https://github.com/oarepo/nrp-devtools/raw/main/tests/forked_install.sh
if test -d $BUILD_TEST_DIR/$MODEL; then
  rm -rf $BUILD_TEST_DIR/$MODEL
fi
oarepo-compile-model ./$CODE_TEST_DIR/$MODEL.yaml --output-directory ./$BUILD_TEST_DIR/$MODEL -vvv

if test -d $TESTS_VENV ; then
	rm -rf $TESTS_VENV
fi
${PYTHON} -m venv $TESTS_VENV
. $TESTS_VENV/bin/activate
pip install -U setuptools pip wheel
pip install "oarepo[tests,rdm]==$OAREPO_VERSION.*"
pip install "./$BUILD_TEST_DIR/${MODEL}[tests]"
pip install ".[tests]"

pytest ./$CODE_TEST_DIR/test_communities
