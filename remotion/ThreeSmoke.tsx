import {ThreeCanvas} from '@remotion/three';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';

/**
 * WebGL smoke test — the walking skeleton for the 3D layer.
 *
 * ⚠️ It exists because three.js's failure mode here is **silence**: under the wrong Chromium OpenGL
 * backend the canvas comes back blank rather than erroring, so "the render exited 0" proves nothing about
 * whether anything was drawn. This composition makes that observable in one still — a coloured lit box on
 * a dark field, or an empty frame.
 *
 * ⚠️ The rotation is read from `useCurrentFrame()`, never R3F's `useFrame()`. `<ThreeCanvas>` forces
 * `frameloop='never'` while rendering, so a `useFrame` animation simply never advances, and the scene
 * would render once and hold.
 *
 * Kept after 0085_09 for the same reason `IndexCard` was kept: when something larger breaks, the smallest
 * thing that exercises the suspect layer is the right thing to reach for.
 */
export const ThreeSmoke = () => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();

  return (
    <AbsoluteFill style={{backgroundColor: '#0b0e13'}}>
      <ThreeCanvas width={width} height={height} camera={{fov: 50, position: [0, 0, 6]}}>
        <ambientLight intensity={0.5} />
        <pointLight position={[4, 5, 6]} intensity={60} />
        {/* Emissive as well as lit, which is the colour rule the scenes will follow: a semantic colour
            that only a light gives meaning to can be shaded out of its own meaning. */}
        <mesh rotation={[frame * 0.02, frame * 0.03, 0]}>
          <boxGeometry args={[2.4, 2.4, 2.4]} />
          <meshStandardMaterial color="#37d67a" emissive="#37d67a" emissiveIntensity={0.35} />
        </mesh>
        {/* A second mesh so a camera/geometry fault cannot be mistaken for a lighting fault. */}
        <mesh position={[-3, -1.6, -1]}>
          <boxGeometry args={[1.2, 1.2, 1.2]} />
          <meshStandardMaterial color="#ff5c5c" emissive="#ff5c5c" emissiveIntensity={0.35} />
        </mesh>
      </ThreeCanvas>
    </AbsoluteFill>
  );
};
