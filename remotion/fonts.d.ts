/**
 * ⚠️ Remotion's webpack config emits fonts as `asset/resource`
 * (`@remotion/bundler/dist/shared-bundler-config.js`), so an imported `.woff2` resolves to a URL **string**
 * and not to a component. Without this declaration `tsc --noEmit` cannot resolve the import at all, and the
 * error surfaces as a red squiggle in the very file that is supposed to be the single source of the typeface.
 */
declare module '*.woff2' {
  const url: string;
  export default url;
}
