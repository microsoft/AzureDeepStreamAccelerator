#dot -Tpng pipeline.dot -o ai-pipeline.png
find -type f -name "*.dot" | xargs dot -Tpng -O
