black oarepo_communities tests --target-version py310
autoflake --in-place --remove-all-unused-imports --recursive oarepo_communities tests
isort oarepo_communities tests  --profile black
