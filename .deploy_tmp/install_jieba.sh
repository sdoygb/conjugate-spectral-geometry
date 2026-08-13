#!/bin/bash
echo 'ab640815.' | sudo -S /usr/local/geometry-ai/venv/bin/pip install jieba 2>&1 | tail -3
echo "---VERIFY---"
echo 'ab640815.' | sudo -S /usr/local/geometry-ai/venv/bin/python3 -c "import jieba; print('jieba OK', jieba.__version__)"
