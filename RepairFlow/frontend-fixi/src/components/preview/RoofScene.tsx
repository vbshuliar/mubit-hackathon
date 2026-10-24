import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Environment, Lightformer, Line, RoundedBox } from "@react-three/drei";
import { useEffect, useRef, useState } from "react";
import { MathUtils, Vector3, type Group } from "three";

type Props = { stage: number; reducedMotion: boolean; active: boolean };
const metal = { color: "#b3bec0", metalness: 0.85, roughness: 0.32 };
const glass = {
  color: "#b2d7d0",
  metalness: 0.12,
  roughness: 0.12,
  transparent: true,
  opacity: 0.25,
  depthWrite: false,
};

function Beam({
  position,
  scale,
  color = metal.color,
}: {
  position: [number, number, number];
  scale: [number, number, number];
  color?: string;
}) {
  return (
    <mesh position={position} scale={scale}>
      <boxGeometry />
      <meshStandardMaterial {...metal} color={color} />
    </mesh>
  );
}

function Building({ stage }: { stage: number }) {
  const scaffold = stage === 1 || stage === 2;
  return (
    <group position={[0, -0.45, 0]}>
      <RoundedBox args={[5.4, 0.18, 4.3]} radius={0.07} position={[0, -0.15, 0]}>
        <meshStandardMaterial color="#465052" metalness={0.75} roughness={0.38} />
      </RoundedBox>
      <RoundedBox args={[4.7, 0.12, 3.65]} radius={0.04} position={[0, -0.01, 0]}>
        <meshStandardMaterial {...metal} />
      </RoundedBox>
      {/* A cutaway architectural model: structure, floor slabs and glazed bays. */}
      {[0.12, 1.35, 2.6].map((y) => (
        <Beam key={y} position={[0, y, 0]} scale={[3.55, 0.12, 2.6]} />
      ))}
      {[-1.68, 0, 1.68].map((x) =>
        [-1.22, 1.22].map((z) => (
          <Beam key={`${x}-${z}`} position={[x, 1.35, z]} scale={[0.09, 2.6, 0.09]} />
        )),
      )}
      {[0.75, 1.98].map((y) =>
        [-0.85, 0.85].map((x) => (
          <mesh key={`${x}-${y}`} position={[x, y, 1.23]}>
            <boxGeometry args={[1.5, 1.08, 0.035]} />
            <meshPhysicalMaterial {...glass} />
          </mesh>
        )),
      )}
      {[-1.69, 1.69].map((x) => (
        <mesh key={x} position={[x, 1.36, 0]}>
          <boxGeometry args={[0.035, 2.35, 2.3]} />
          <meshPhysicalMaterial {...glass} />
        </mesh>
      ))}
      <mesh position={[0, 1.35, -1.23]}>
        <boxGeometry args={[3.3, 2.4, 0.05]} />
        <meshStandardMaterial color="#879595" metalness={0.5} roughness={0.6} />
      </mesh>
      <Beam position={[-0.55, 0.7, 0]} scale={[0.08, 1.15, 2.4]} />
      <Beam position={[0.8, 1.98, 0]} scale={[1.5, 0.08, 1.7]} color="#718c86" />
      {/* Two metal roof planes meet at a ridge; the highlighted flashing marks the issue. */}
      {[-1, 1].map((side) => (
        <group key={side} position={[side * 0.91, 2.98, 0]} rotation={[0, 0, -side * 0.4]}>
          <mesh>
            <boxGeometry args={[2.02, 0.09, 2.95]} />
            <meshStandardMaterial {...metal} color={stage === 3 ? "#9db8ad" : "#9aa5a8"} />
          </mesh>
          {[-1.25, -0.95, -0.65, -0.35, 0, 0.35, 0.65, 0.95, 1.25].map((z) => (
            <Beam key={z} position={[0, 0.06, z]} scale={[2, 0.018, 0.018]} color="#d9dfdc" />
          ))}
        </group>
      ))}
      <Beam
        position={[0, 3.37, 0]}
        scale={[0.1, 0.1, 3]}
        color={stage === 3 ? "#67ba98" : "#c8d0d0"}
      />
      <Beam position={[0.7, 3.5, -0.65]} scale={[0.35, 0.75, 0.4]} color="#748082" />
      <mesh position={[0.7, 3.14, -0.4]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.19, 0.25, 40]} />
        <meshBasicMaterial color={stage === 3 ? "#73e3b5" : "#efb978"} side={2} />
      </mesh>
      {scaffold && (
        <group position={[0, 0, 1.7]}>
          {[-2, -0.65, 0.65, 2].map((x) =>
            [0, 0.6].map((z) => (
              <Beam
                key={`${x}-${z}`}
                position={[x, 1.52, z]}
                scale={[0.045, 3.1, 0.045]}
                color={stage === 2 ? "#88b7a3" : "#a9afb0"}
              />
            )),
          )}
          {[0.5, 1.55, 2.6].map((y) => (
            <group key={y}>
              <Beam position={[0, y, 0.3]} scale={[4.25, 0.065, 0.78]} />
              <Beam position={[0, y + 0.45, 0.6]} scale={[4.2, 0.04, 0.04]} />
            </group>
          ))}
          {[-1.33, 0, 1.33].map((x) => (
            <mesh key={x} position={[x, 1.55, 0.61]} rotation={[0, 0, 0.55]}>
              <boxGeometry args={[0.035, 2.5, 0.035]} />
              <meshStandardMaterial {...metal} />
            </mesh>
          ))}
        </group>
      )}
      <Line
        points={
          stage === 0
            ? [
                [-2.4, 0.25, 1],
                [-2.4, 3.6, 1],
                [0.7, 3.6, -0.4],
              ]
            : stage === 3
              ? [
                  [-2.4, 0.25, 1],
                  [-2.4, 0.25, 2.5],
                  [2.5, 0.25, 2.5],
                  [2.5, 2.9, 0],
                ]
              : [
                  [2.4, 0.3, 2.2],
                  [2.4, 3.6, 2.2],
                  [0.7, 3.6, -0.4],
                ]
        }
        color={stage === 3 ? "#72c9a7" : "#b0bbb8"}
        lineWidth={1}
        dashed
        dashSize={0.08}
        gapSize={0.07}
      />
      {stage === 3 && (
        <mesh position={[2.45, 0.12, 1.6]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.25, 0.32, 40]} />
          <meshBasicMaterial color="#73e3b5" />
        </mesh>
      )}
    </group>
  );
}

function StageCamera({ stage, reducedMotion, active }: Props) {
  const { camera, invalidate, gl } = useThree();
  const target = useRef(new Vector3());
  const [lost, setLost] = useState(false);
  useEffect(() => {
    const onLost = (event: Event) => {
      event.preventDefault();
      setLost(true);
    };
    gl.domElement.addEventListener("webglcontextlost", onLost);
    return () => gl.domElement.removeEventListener("webglcontextlost", onLost);
  }, [gl]);
  useEffect(() => {
    invalidate();
  }, [stage, reducedMotion, active, invalidate]);
  useFrame((_, delta) => {
    const angle = 0.68 + stage * 0.09;
    target.current.set(Math.sin(angle) * 8, 5.4, Math.cos(angle) * 8);
    if (reducedMotion) camera.position.copy(target.current);
    else camera.position.lerp(target.current, 1 - Math.exp(-Math.min(delta, 0.05) * 4));
    camera.lookAt(0, 1.1, 0);
    if (active && !reducedMotion && camera.position.distanceTo(target.current) > 0.002)
      invalidate();
  });
  if (lost) throw new Error("WebGL context lost");
  return null;
}

export default function RoofScene(props: Props) {
  return (
    <Canvas
      dpr={[1, 1.5]}
      frameloop={props.active ? "demand" : "never"}
      camera={{ position: [5, 5.4, 6.3], fov: 38 }}
      gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
      fallback={
        <div className="scene-fallback">
          3D unavailable. Use the stage explanation beside the model.
        </div>
      }
    >
      <ambientLight intensity={0.8} />
      <directionalLight position={[4, 8, 5]} intensity={3} />
      <directionalLight position={[-4, 3, -3]} color="#a8c7c5" intensity={2} />
      <Environment resolution={128} frames={1}>
        <Lightformer intensity={3} position={[0, 5, -4]} scale={[8, 3, 1]} />
        <Lightformer
          intensity={2}
          position={[-5, 2, 1]}
          rotation={[0, Math.PI / 2, 0]}
          scale={[5, 5, 1]}
        />
      </Environment>
      <Building stage={props.stage} />
      <StageCamera {...props} />
    </Canvas>
  );
}
