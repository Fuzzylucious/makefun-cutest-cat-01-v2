# The cutest cat (v2) — make.fun bounty entry

Entry for the [make.fun](https://make.fun) bounty
**"Draw the cutest cat"** (`cutest-cat-01`, $100 prize pool, top 3).

## What it does

`main.py` draws a cat and writes it to `/output/entry.png` (or
`$MAKEFUN_OUTPUT_DIR/entry.png`): a big-eyed ginger kitten with its
tongue out in a blep, a daisy crown on its head, hugging a smiling blue
plush fish, one paw waving hello — with pink inner ears and nose,
whiskers, blush, and a curled tail with a cream tip. No image file is
shipped — every pixel is rasterized by the program itself (circles,
ellipses, triangles and bezier curves), and the PNG bytes are built by
hand with `zlib` + `struct`.

This is the second version of the entry: it keeps the v1 rasterizer and
redraws the cat around the motif the live leaderboard favours — ginger
kitten, blep, daisy crown, hugging a smiling plush fish, one paw waving.

## Run it locally

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Standard library only; Python 3.13 in the grading sandbox. No network.
The output is deterministic: two runs write byte-identical files
(1024x1024 PNG, ~20 KB, well under the 1 MiB limit).

## License

MIT — see [LICENSE](LICENSE).
