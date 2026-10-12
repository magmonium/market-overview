import {Config} from '@remotion/cli/config';

/**
 * ⚠️ **Required for the 3D layer, and it fails quietly without it.**
 *
 * three.js does not render under Chromium's default OpenGL backend — the canvas comes back blank rather
 * than erroring, which is the worst possible way for it to fail. Remotion's own guidance for React Three
 * Fiber is the ANGLE backend. Server-side render APIs need the same setting passed explicitly as
 * `chromiumOptions: {gl: 'angle'}`.
 */
Config.setChromiumOpenGlRenderer('angle');
