#!/usr/bin/bash

rm -rf ./test_files/*
rm -rf ./grounded_context.json

source .venv/bin/activate

for f in ./test_docs/*; do
    if [[ -f "$f" ]]; then
        fout="${f//test_docs/test_files}"
        python ./pdf_parser.py "${f}" --json "${fout//.pdf/.json}"
        python ./json_to_md.py --input_filename "${fout//.pdf/.json}"
    fi
done

python ./eval_llms.py grounded_context.json
python ./analyze_results.py
