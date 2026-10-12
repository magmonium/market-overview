import {useLayoutEffect, useMemo, useRef} from 'react';
import * as THREE from 'three';
import {DOWN, HORIZON, RIM, TERRAIN, TILE, UP, seeded} from './theme';

/**
 * The primitive set — **six shapes, closed.** Issue 12: "Every scene is built from these, and no scene
 * invents a seventh." Reusing a small set is what makes ten blocks read as one product rather than ten
 * demos.
 *
 * ⚠️ **Instances are static; the camera and the group transform carry the motion.** Nothing here animates
 * per instance, which keeps the scene deterministic and keeps the per-frame cost on the camera rather than
 * on rebuilding matrices — and it matches issue 12's first camera rule, that depth comes from moving.
 */

/** Places every instance once, from a memoised matrix list. Deterministic by construction. */
const useInstances = (matrices: THREE.Matrix4[]) => {
  const ref = useRef<THREE.InstancedMesh>(null);
  useLayoutEffect(() => {
    const mesh = ref.current;
    if (!mesh) {
      return;
    }
    matrices.forEach((matrix, index) => mesh.setMatrixAt(index, matrix));
    mesh.instanceMatrix.needsUpdate = true;
  }, [matrices]);
  return ref;
};

const grid = (count: number, columns: number, spacing: number, z = 0) =>
  Array.from({length: count}, (_, index) => ({
    x: index % columns,
    row: z + Math.floor(index / columns),
  }));

/** 1 — `terrain`: the reflective ground plane, the world's floor, **tinted by the day's direction**. */
export const Terrain = ({leanPercent}: {leanPercent: number}) => (
  <>
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.2, -6]}>
      <planeGeometry args={[90, 46]} />
      {/* Low roughness + metalness is what gives the sheen. There is no environment map, so the light rig
          is the whole of the reflection — which keeps it deterministic and dependency-free. */}
      <meshStandardMaterial
        color={leanPercent >= 0 ? TERRAIN : '#1c1418'}
        roughness={0.42}
        metalness={0.5}
      />
    </mesh>
    {/* The horizon rim, so the plane reads as a world rather than a rectangle. */}
    <mesh position={[0, -1.14, -28]}>
      <boxGeometry args={[90, 0.06, 0.06]} />
      <meshStandardMaterial color={RIM} emissive={RIM} emissiveIntensity={0.35} />
    </mesh>
  </>
);

/** 2 — `column`: an instanced extruded bar, **magnitude as height**. */
export const Columns = ({
  values,
  spacing = 1.5,
  z = 0,
  width = 0.7,
  positive = true,
}: {
  values: number[];
  spacing?: number;
  z?: number;
  width?: number;
  positive?: boolean;
}) => {
  const matrices = useMemo(() => {
    const columns = Math.max(values.length, 1);
    return values.map((value, index) => {
      const {x, row} = grid(values.length, columns, spacing, z)[index];
      const height = Math.max(0.25, Math.abs(value));
      // ⚠️ Grown from the floor, not scaled about its centre — a bar that grows both ways reads as
      // hovering, which loses "magnitude as height" entirely.
      return new THREE.Matrix4().compose(
        new THREE.Vector3(x - ((columns - 1) * spacing) / 2, -1.2 + height / 2, row),
        new THREE.Quaternion(),
        new THREE.Vector3(width, height, 0.55)
      );
    });
  }, [values, spacing, z, width]);

  const ref = useInstances(matrices);
  return (
    <instancedMesh ref={ref} args={[undefined, undefined, Math.max(values.length, 1)]}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial
        color={positive ? UP : DOWN}
        emissive={positive ? UP : DOWN}
        emissiveIntensity={0.3}
        roughness={0.35}
      />
    </instancedMesh>
  );
};

/** 3 — `tile`: a flat quad used in grids. The scoreboard and heat-map backdrop. */
export const Tiles = ({
  count,
  columns,
  spacing = 2.2,
  z = 0,
  size = 1.9,
  color,
}: {
  count: number;
  columns: number;
  spacing?: number;
  z?: number;
  size?: number;
  color?: string;
}) => {
  const matrices = useMemo(
    () =>
      grid(count, columns, spacing, z).map(({x, row}) =>
        new THREE.Matrix4().compose(
          new THREE.Vector3(x * spacing - ((columns - 1) * spacing) / 2, -1.15, row),
          new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0)),
          new THREE.Vector3(size, size * 1.15, 1)
        )
      ),
    [count, columns, spacing, z, size]
  );
  const ref = useInstances(matrices);
  return (
    <instancedMesh ref={ref} args={[undefined, undefined, Math.max(count, 1)]}>
      <planeGeometry args={[1, 1]} />
      <meshStandardMaterial
        color={color ?? TILE}
        emissive={color ?? TILE}
        emissiveIntensity={0.5}
        roughness={0.5}
        side={THREE.DoubleSide}
        transparent
        opacity={0.85}
      />
    </instancedMesh>
  );
};

/** 4 — `ring`: a concentric torus. The gauge family. */
export const Rings = ({radii = [2.6, 3.6, 4.6]}: {radii?: number[]}) => (
  <>
    {radii.map((radius, index) => (
      <mesh key={radius} position={[0, -0.9, 0]} rotation={[-Math.PI / 2.4, 0, index * 0.22]}>
        <torusGeometry args={[radius, 0.045, 12, 96]} />
        <meshStandardMaterial color={RIM} emissive={RIM} emissiveIntensity={0.4} />
      </mesh>
    ))}
  </>
);

/** 5 — `particle`: instanced points. Breadth flow and dependency drift.
 *
 * ⚠️ Takes a **seed string**, not a generator function. A shared stateful generator would produce a
 * different field depending on how many times it had already been called — so scrubbing, a re-render, or a
 * second edition could place the particles somewhere else and the frame would stop being deterministic.
 * A seed makes the field a pure function of its inputs. */
export const Particles = ({
  count,
  seed,
  spread = [26, 6, 16] as [number, number, number],
  color = RIM,
}: {
  count: number;
  seed: string;
  spread?: [number, number, number];
  color?: string;
}) => {
  const positions = useMemo(() => {
    const random = seeded(seed);
    const buffer = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      buffer[i * 3] = (random() - 0.5) * spread[0];
      buffer[i * 3 + 1] = (random() - 0.5) * spread[1];
      buffer[i * 3 + 2] = (random() - 0.5) * spread[2] - 4;
    }
    return buffer;
  }, [count, seed, spread]);

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.07} color={color} sizeAttenuation transparent opacity={0.6} />
    </points>
  );
};

/** 6 — `rig`: the fixed key / rim / ambient light rig. Fixed, so the same value lights the same on every
 * run and a re-render matches. */
export const Rig = () => (
  <>
    <ambientLight intensity={0.35} />
    <directionalLight color="#dce6f5" position={[6, 12, 8]} intensity={1.5} />
    <directionalLight color={RIM} position={[-9, 4, -7]} intensity={0.7} />
    <fog attach="fog" args={[HORIZON, 16, 44]} />
  </>
);

export const tone = (value: number | null | undefined) => ((value ?? 0) >= 0 ? UP : DOWN);

