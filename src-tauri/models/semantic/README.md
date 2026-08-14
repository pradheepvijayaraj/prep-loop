# Bundled Semantic Search Model

The Rust backend uses the quantized `Xenova/paraphrase-MiniLM-L3-v2` ONNX
model for fully offline sentence embeddings. The upstream model is based on
`sentence-transformers/paraphrase-MiniLM-L3-v2` and is distributed under the
Apache-2.0 license.

Only the quantized model and four tokenizer/configuration files are bundled.
The generated binary also stores one UPSC-syllabus main tag, up to three
subtags, and a compact taxonomy vector for every question. Section constraints
are applied before ranking, so searches outside Mathematics never score the
Mathematics records.

Regenerate the compact question index after changing the corpus with:

```sh
bun run semantic:index
```
