/**
 * The render layer's entry point — the file `remotion render` is pointed at.
 *
 * ⚠️ **It lives in the nested project while Remotion itself comes from the parent's `node_modules`**, so nothing is
 * installed twice: the CLI is resolved by walking up from this folder, and the bundled toolchain it ships (`ffmpeg`)
 * is the one the Python side already uses.
 *
 * ⚠️ **Both projects have a file by this name**, which is why `render.where()` runs the render from *this* tree — the
 * reel's `where()` records what happens otherwise: *"Run the render from the repository and Remotion bundles the
 * brief's root, then reports a missing composition and helpfully lists `MarketBrief, Thumbnail, IndexCard`."*
 */
import {registerRoot} from 'remotion';
import {RemotionRoot} from './Root.tsx';

registerRoot(RemotionRoot);
