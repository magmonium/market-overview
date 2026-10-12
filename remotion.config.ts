/**
 * The Remotion config.
 *
 * ⚠️ **This file used to pin Chromium's OpenGL backend to ANGLE** — `Config.setChromiumOpenGlRenderer('angle')`,
 * which three.js needed because it fails *silently* under the default backend: the canvas comes back blank rather
 * than erroring, which is the worst possible way for it to fail. The 3D world has been replaced by a fully DOM
 * backdrop (`remotion/Backdrop.tsx`), so there is no WebGL context left to pin and the setting is gone.
 *
 * The file is kept, rather than deleted, so the removal of that requirement is visible here rather than only in
 * a deleted line — and as the place a future render setting belongs.
 */
export {};

