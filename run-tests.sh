#!/bin/bash
set -e

MODEL="thesis"
CODE_TEST_DIR="tests"
BUILD_TEST_DIR="tests"

BUILDER_VENV=".venv-builder"
TESTS_VENV=".venv-tests"

OAREPO_VERSION=${OAREPO_VERSION:-11}

if test -d $BUILDER_VENV ; then
	rm -rf $BUILDER_VENV
fi
python3 -m venv $BUILDER_VENV
. $BUILDER_VENV/bin/activate
pip install -U setuptools pip wheel
pip install oarepo-model-builder oarepo-model-builder-requests oarepo-model-builder-drafts oarepo-model-builder-communities
#editable_install /home/ron/prace/oarepo-model-builder-drafts
#editable_install /home/ron/prace/oarepo-model-builder-communities
if test -d $BUILD_TEST_DIR/$MODEL; then
  rm -rf $BUILD_TEST_DIR/$MODEL
fi
oarepo-compile-model ./$CODE_TEST_DIR/$MODEL.yaml --output-directory ./$BUILD_TEST_DIR/$MODEL -vvv


if test -d $TESTS_VENV ; then
	rm -rf $TESTS_VENV
fi
python3 -m venv $TESTS_VENV
. $TESTS_VENV/bin/activate
pip install -U setuptools pip wheel
pip install "oarepo[tests]==${OAREPO_VERSION}.*"
pip install "./$BUILD_TEST_DIR/${MODEL}[tests]"
pip install .
#editable_install /home/ron/prace/oarepo-requests
pytest ./$CODE_TEST_DIR/test_communities
