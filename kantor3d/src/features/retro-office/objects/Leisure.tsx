"use client";
// kantorai: furnitur pojok santai — TV (layar berpendar) dan kasur.

import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";
import { SCALE } from "@/features/retro-office/core/constants";
import {
  getItemBaseSize,
  getItemRotationRadians,
  toWorld,
} from "@/features/retro-office/core/geometry";
import type { InteractiveFurnitureModelProps } from "@/features/retro-office/objects/types";

type GroupHandlers = Pick<
  InteractiveFurnitureModelProps,
  "item" | "onPointerDown" | "onPointerOver" | "onPointerOut" | "onClick"
>;

function useFootprint(item: InteractiveFurnitureModelProps["item"]) {
  const [wx, , wz] = toWorld(item.x, item.y);
  const { width, height } = getItemBaseSize(item);
  return {
    wx,
    wz,
    w: width * SCALE,
    d: height * SCALE,
    rotY: getItemRotationRadians(item),
  };
}

function Interactive({
  item,
  onPointerDown,
  onPointerOver,
  onPointerOut,
  onClick,
  position,
  children,
}: GroupHandlers & { position: [number, number, number]; children: React.ReactNode }) {
  return (
    <group
      position={position}
      onPointerDown={(e) => {
        e.stopPropagation();
        onPointerDown(item._uid);
      }}
      onPointerOver={(e) => {
        e.stopPropagation();
        onPointerOver(item._uid);
      }}
      onPointerOut={(e) => {
        e.stopPropagation();
        onPointerOut();
      }}
      onClick={(e) => {
        e.stopPropagation();
        onClick?.(item._uid);
      }}
    >
      {children}
    </group>
  );
}

const TV_COLORS = ["#b91c1c", "#7c3aed", "#0ea5e9", "#f59e0b", "#16a34a"].map(
  (c) => new THREE.Color(c),
);

export function TvModel(props: InteractiveFurnitureModelProps) {
  const { item, isSelected, isHovered } = props;
  const { wx, wz, w, d, rotY } = useFootprint(item);
  const screenMat = useRef<THREE.MeshStandardMaterial>(null);
  const tmp = useRef(new THREE.Color());

  useFrame((state) => {
    const mat = screenMat.current;
    if (!mat) return;
    // Ganti "adegan" tiap 3 detik dengan transisi halus, plus kedip kecil seperti film.
    const t = state.clock.elapsedTime / 3;
    const i = Math.floor(t) % TV_COLORS.length;
    const next = (i + 1) % TV_COLORS.length;
    tmp.current.copy(TV_COLORS[i]).lerp(TV_COLORS[next], t % 1);
    mat.emissive.copy(tmp.current);
    mat.emissiveIntensity = 0.75 + Math.sin(state.clock.elapsedTime * 9) * 0.08;
  });

  const highlighted = isSelected || isHovered;
  const screenW = w * 0.92;
  const screenH = screenW * 0.56;
  const standH = 0.75;

  return (
    <Interactive {...props} position={[wx, 0, wz]}>
      <group position={[w / 2, 0, d / 2]} rotation={[0, rotY, 0]}>
        {/* Kaki dan tiang. */}
        <mesh position={[0, 0.03, 0]} castShadow receiveShadow>
          <boxGeometry args={[w * 0.5, 0.06, d * 0.9]} />
          <meshStandardMaterial color="#1f2937" roughness={0.6} />
        </mesh>
        <mesh position={[0, standH / 2, -d * 0.1]} castShadow>
          <boxGeometry args={[0.08, standH, 0.08]} />
          <meshStandardMaterial color="#111827" roughness={0.5} />
        </mesh>
        {/* Bingkai. */}
        <mesh position={[0, standH + screenH / 2, -d * 0.1]} castShadow>
          <boxGeometry args={[w, screenH + 0.08, 0.08]} />
          <meshStandardMaterial color={highlighted ? "#374151" : "#0b0d12"} roughness={0.4} />
        </mesh>
        {/* Layar. */}
        <mesh position={[0, standH + screenH / 2, -d * 0.1 + 0.045]}>
          <planeGeometry args={[screenW, screenH]} />
          <meshStandardMaterial ref={screenMat} color="#111111" emissive="#b91c1c" emissiveIntensity={0.75} />
        </mesh>
      </group>
    </Interactive>
  );
}

export function BedModel(props: InteractiveFurnitureModelProps) {
  const { item, isSelected, isHovered } = props;
  const { wx, wz, w, d, rotY } = useFootprint(item);
  const highlighted = isSelected || isHovered;
  const blanket = item.color ?? "#93c5fd";

  return (
    <Interactive {...props} position={[wx, 0, wz]}>
      <group position={[w / 2, 0, d / 2]} rotation={[0, rotY, 0]}>
        {/* Rangka kayu. */}
        <mesh position={[0, 0.12, 0]} castShadow receiveShadow>
          <boxGeometry args={[w, 0.24, d]} />
          <meshStandardMaterial color={highlighted ? "#b07b4f" : "#8b5a33"} roughness={0.8} />
        </mesh>
        {/* Sandaran kepala (sisi -z). */}
        <mesh position={[0, 0.4, -d / 2 + 0.04]} castShadow>
          <boxGeometry args={[w, 0.56, 0.08]} />
          <meshStandardMaterial color="#7a4b2a" roughness={0.8} />
        </mesh>
        {/* Kasur. */}
        <mesh position={[0, 0.3, 0.02]} castShadow receiveShadow>
          <boxGeometry args={[w * 0.94, 0.14, d * 0.92]} />
          <meshStandardMaterial color="#f8fafc" roughness={0.9} />
        </mesh>
        {/* Selimut. */}
        <mesh position={[0, 0.385, d * 0.14]} castShadow>
          <boxGeometry args={[w * 0.96, 0.04, d * 0.6]} />
          <meshStandardMaterial color={blanket} roughness={0.95} />
        </mesh>
        {/* Bantal. */}
        <mesh position={[0, 0.41, -d / 2 + 0.2]} castShadow>
          <boxGeometry args={[w * 0.7, 0.1, 0.22]} />
          <meshStandardMaterial color="#ffffff" roughness={0.95} />
        </mesh>
      </group>
    </Interactive>
  );
}
