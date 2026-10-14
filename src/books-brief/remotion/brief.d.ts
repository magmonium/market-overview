/**
 * ⚠️ **The brief's module declarations, pulled in by reference rather than copied.**
 *
 * The charts are set in the brief's **own vendored faces** (`../../../remotion/fonts.ts`), and that file imports nine
 * `.woff2` assets. Remotion's bundler emits them as `asset/resource`, so an import resolves to a URL *string* — and
 * without the ambient `*.woff2` declaration in the program, `tsc --noEmit` cannot resolve them at all.
 *
 * The declaration already exists, next door, and a second copy of it would be a second thing to keep in step. A
 * `reference` is how one file's ambient declarations join another project's program.
 */
/// <reference path="../../../remotion/fonts.d.ts" />
