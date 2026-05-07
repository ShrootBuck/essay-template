#!/bin/bash

WORD_COUNT=$(sed -n '/<!-- START_WORD_COUNT -->/,/<!-- END_WORD_COUNT -->/p' Essay.md | sed 's/<!--.*-->//' | wc -w | tr -d ' ')

sed "s/\[Insert Word Count Here\]/$WORD_COUNT/" Essay.md > Essay_temp.md
pandoc Essay_temp.md -o Essay.pdf --pdf-engine=xelatex
rm Essay_temp.md

echo "Word count: $WORD_COUNT"
