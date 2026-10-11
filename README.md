# cellstr

Display-cell-accurate len, slice, pad and truncate for strings with ANSI codes and wide characters

## Install

```
pip install cellstr
```

## Usage

`str.ljust`, slicing and `len` all count code points, so they misalign any text
that carries colour codes, CJK characters or combining marks. `cellstr` counts
the cells a terminal actually draws.

```python
from cellstr import cell_len, cell_slice, ljust, truncate

warn = "\x1b[31mWARN\x1b[0m"      # red "WARN"
cell_len(warn)                    # 4, the escape codes do not count
cell_len("你好")          # 4, two wide characters

cell_slice(warn, 0, 2)            # "\x1b[31mWA\x1b[0m", colour kept
cell_slice("a你b", 0, 2)      # "a", the wide char would overflow and is dropped

ljust("你", 4)                # "你  ", padded to four cells
truncate("hello world", 8)        # "hello..."
```

Every function ignores ANSI escape sequences when measuring and keeps them in
place when slicing or padding, so styled output stays styled. Wide, fullwidth,
zero-width and combining characters are measured from a vendored Unicode width
table, so there is no runtime dependency.

Public API: `cell_len`, `char_width`, `cell_slice`, `ljust`, `rjust`, `center`,
`truncate`, `strip_ansi`, and `UNICODE_VERSION`.

## Why

Aligning terminal text breaks the moment it contains colour or non-Latin
characters, and the existing tools each solve only part of it. `strip-ansi` and
`ansiwrap` remove escapes but know nothing about character width, and both ship
untyped. `wcwidth` measures plain-text width well and is the right primitive for
that job, but it does not give you a typed, cohesive set of string operations:
slicing by column that preserves escapes, padding, and width-aware truncation
with a suffix. `cellstr` fills that gap in one small, fully typed, zero-dependency
package: measure, slice, pad and truncate by the cells a terminal draws, with
ANSI sequences and wide, zero-width and combining characters all accounted for.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
