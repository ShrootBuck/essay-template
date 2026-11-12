#!/bin/sh
set -eu
cd "$(dirname "$0")"
exec typst compile Essay.typ Essay.pdf
