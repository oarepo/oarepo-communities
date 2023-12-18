#!/bin/bash
set -e

# temporarily disabled tests before we remove the requirement
# for communities<6 (it is already in oarepo requirements)
exit 0

MODEL="thesis"
CODE_TEST_DIR="tests"
BUILD_TEST_DIR="tests"

BUILDER_VENV=".venv-builder"
TESTS_VENV=".venv-tests"

OAREPO_VERSION=${OAREPO_VERSION:-11}
OAREPO_VERSION_MAX=$((OAREPO_VERSION+1))

if test -d $BUILDER_VENV ; then
	rm -rf $BUILDER_VENV
fi
python3 -m venv $BUILDER_VENV
. $BUILDER_VENV/bin/activate
pip install -U setuptools pip wheel
pip install oarepo-model-builder oarepo-model-builder-drafts oarepo-model-builder-communities
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
pip install "oarepo>=$OAREPO_VERSION,<$OAREPO_VERSION_MAX"
pip install "./$BUILD_TEST_DIR/$MODEL[tests]"
pip install .
pip uninstall -y uritemplate
pip install uritemplate
pytest ./$CODE_TEST_DIR/test_permissions
