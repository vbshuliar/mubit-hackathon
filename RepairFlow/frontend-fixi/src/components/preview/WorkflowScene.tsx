import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Environment, Lightformer, RoundedBox, Line } from "@react-three/drei";
import { useEffect, useRef, type RefObject } from "react";
import { Group, MathUtils, Vector3 } from "three";
import { Building } from "./RoofScene";

type Props = {
  progress: RefObject<number>;
  stage: number;
  active: boolean;
  reducedMotion: boolean;
};

function Assembly({ progress, stage, reducedMotion, active }: Props) {
  const building = useRef<Group>(null);
  const chip = useRef<Group>(null);
  const rings = useRef<Group>(null);
  const { camera, invalidate } = useThree();
  const target = useRef(new Vector3());
  useEffect(() => {
    invalidate();
  }, [stage, reducedMotion, invalidate]);
  useEffect(() => {
    if (!active || reducedMotion) return;
    const redraw = () => invalidate();
    window.addEventListener("scroll", redraw, { passive: true });
    window.addEventListener("resize", redraw);
    invalidate();
    return () => {
      window.removeEventListener("scroll", redraw);
      window.removeEventListener("resize", redraw);
    };
  }, [active, reducedMotion, invalidate]);
  useFrame((_, delta) => {
    const p = reducedMotion ? stage : progress.current;
    const blend = MathUtils.smoothstep(p, 3.7, 4);
    const alpha = reducedMotion ? 1 : 1 - Math.exp(-Math.min(delta, 0.05) * 6);
    if (building.current) {
      building.current.scale.setScalar(Math.max(0.001, 1 - blend));
      building.current.rotation.y = -0.3 + Math.min(p, 3.7) * 0.25;
      building.current.position.y = -0.35 - blend * 2;
    }
    if (chip.current) {
      chip.current.scale.setScalar(Math.max(0.001, blend));
      chip.current.rotation.y = -0.45 + (p - 4) * 0.3;
      chip.current.position.y = 0.8;
    }
    if (rings.current) rings.current.rotation.y = p * 0.3;
    target.current.set(6.6 - blend * 1.4, 5.1 + blend, 8.3);
    camera.position.lerp(target.current, alpha);
    camera.lookAt(0, 0.9, 0);
    if (active && !reducedMotion && camera.position.distanceTo(target.current) > 0.002)
      invalidate();
  });
  return (
    <>
      <group ref={building}>
        <Building stage={Math.min(stage, 3)} />
      </group>
      <group ref={chip} scale={0.001}>
        {[-0.75, -0.32, 0.16, 0.65].map((y, i) => (
          <RoundedBox
            key={y}
            args={[3.3 - i * 0.18, 0.15, 3.3 - i * 0.18]}
            radius={0.12}
            smoothness={4}
            position={[0, y, 0]}
          >
            <meshPhysicalMaterial
              color={i === 3 ? "#acdeca" : "#a8b8ba"}
              metalness={i === 3 ? 0.45 : 0.9}
              roughness={0.2}
              transparent
              opacity={i === 1 ? 0.35 : 1}
            />
          </RoundedBox>
        ))}
        <RoundedBox args={[1.6, 0.26, 1.6]} position={[0, 0.87, 0]} radius={0.12}>
          <meshStandardMaterial color="#223c35" metalness={0.8} roughness={0.23} />
        </RoundedBox>
        {[-1, 1].flatMap((side) =>
          Array.from({ length: 9 }, (_, i) => (
            <group key={`${side}-${i}`}>
              <mesh position={[side * 1.9, -0.7, -1.3 + i * 0.32]}>
                <boxGeometry args={[0.55, 0.06, 0.11]} />
                <meshStandardMaterial color="#b3c0bd" metalness={0.9} roughness={0.2} />
              </mesh>
              <mesh position={[-1.3 + i * 0.32, -0.7, side * 1.9]}>
                <boxGeometry args={[0.11, 0.06, 0.55]} />
                <meshStandardMaterial color="#b3c0bd" metalness={0.9} roughness={0.2} />
              </mesh>
            </group>
          )),
        )}
        <group ref={rings}>
          {[2.5, 3.05].map((radius, i) => (
            <mesh key={radius} rotation={[-Math.PI / 2, i * 0.2, i * 0.15]} position={[0, -0.5, 0]}>
              <torusGeometry args={[radius, 0.015, 8, 100]} />
              <meshBasicMaterial color={i === 0 ? "#79d5b1" : "#566a65"} />
            </mesh>
          ))}
        </group>
        {[0, 1, 2, 3].map((i) => (
          <group key={i} rotation={[0, (i * Math.PI) / 2, 0]}>
            <Line
              points={[
                [1.8, -0.65, 0],
                [2.7, -0.65, 0],
                [2.7, 0.7, 0],
              ]}
              color="#70bd9e"
              lineWidth={1.2}
            />
            <mesh position={[2.7, 0.7, 0]}>
              <sphereGeometry args={[0.09, 16, 16]} />
              <meshStandardMaterial color="#9af0c9" emissive="#4d9c7c" emissiveIntensity={0.4} />
            </mesh>
          </group>
        ))}
      </group>
    </>
  );
}

export default function WorkflowScene(props: Props) {
  return (
    <Canvas
      dpr={[1, 1.5]}
      frameloop="demand"
      camera={{ position: [6.6, 5.1, 8.3], fov: 37 }}
      gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
      fallback={
        <div className="workflow-diagram">
          3D is unavailable. Select Diagram view to explore the workflow.
        </div>
      }
    >
      <ambientLight intensity={1.2} />
      <directionalLight position={[3, 8, 5]} intensity={3} />
      <directionalLight position={[-4, 3, -3]} color="#b0e5d1" intensity={2} />
      <Environment resolution={128} frames={1}>
        <Lightformer intensity={4} position={[0, 6, -4]} scale={[10, 4, 1]} />
        <Lightformer
          intensity={3}
          position={[-5, 2, 1]}
          rotation={[0, Math.PI / 2, 0]}
          scale={[5, 5, 1]}
        />
      </Environment>
      <Assembly {...props} />
    </Canvas>
  );
}
