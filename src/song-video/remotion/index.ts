/**
 * The render layer's entry point — the file `remotion render` / `remotion still` is pointed at.
 *
 * ⚠️ It lives in the **nested** project while Remotion itself comes from the parent's `node_modules`, so
 * nothing is installed twice: the CLI is resolved by walking up from this folder, and the bundled toolchain it
 * ships (`ffmpeg`, `ffprobe`) is the one the Python side already uses.
 */
import {registerRoot} from 'remotion';
import {RemotionRoot} from './Root.tsx';

registerRoot(RemotionRoot);
