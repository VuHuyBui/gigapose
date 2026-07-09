import argparse
import json
import re
from pathlib import Path

import numpy as np
import trimesh


def get_obj_id(path: Path) -> int:
    """
    Extract BOP object ID from names like:
        obj_000001.ply -> 1
        obj_000023.ply -> 23
    """
    match = re.match(r"obj_(\d+)\.(ply|obj)$", path.name)
    if not match:
        raise ValueError(
            f"Bad model filename: {path.name}. "
            "Expected format like obj_000001.ply"
        )
    return int(match.group(1))


def load_vertices(model_path: Path) -> np.ndarray:
    mesh = trimesh.load(model_path, force="mesh", process=False)

    # If trimesh loads a Scene, merge all geometry.
    if isinstance(mesh, trimesh.Scene):
        meshes = list(mesh.geometry.values())
        mesh = trimesh.util.concatenate(meshes)

    vertices = np.asarray(mesh.vertices, dtype=np.float64)

    if vertices.ndim != 2 or vertices.shape[1] != 3:
        raise ValueError(f"Could not read Nx3 vertices from {model_path}")

    if len(vertices) == 0:
        raise ValueError(f"No vertices found in {model_path}")

    return vertices


def compute_diameter_chunked(vertices: np.ndarray, chunk_size: int = 2000) -> float:
    """
    Exact max pairwise vertex distance, computed in chunks to avoid creating
    a huge NxN matrix all at once.

    This can still be slow for very large meshes.
    """
    n = len(vertices)
    max_dist_sq = 0.0

    for i in range(0, n, chunk_size):
        a = vertices[i:i + chunk_size]

        # Compare this chunk to all vertices.
        # Shape: (chunk, n, 3)
        diff = a[:, None, :] - vertices[None, :, :]
        dist_sq = np.sum(diff * diff, axis=2)

        chunk_max = float(np.max(dist_sq))
        if chunk_max > max_dist_sq:
            max_dist_sq = chunk_max

    return float(np.sqrt(max_dist_sq))


def compute_models_info(models_dir: Path, scale: float, approximate_large: bool):
    models_info = {}

    model_paths = sorted(models_dir.glob("obj_*.ply")) + sorted(models_dir.glob("obj_*.obj"))

    if not model_paths:
        raise FileNotFoundError(
            f"No obj_*.ply or obj_*.obj files found in {models_dir}"
        )

    for model_path in model_paths:
        obj_id = get_obj_id(model_path)
        vertices = load_vertices(model_path)

        # Use this if your mesh is in meters and you need millimeters:
        # scale=1000.0
        vertices = vertices * scale

        mins = vertices.min(axis=0)
        maxs = vertices.max(axis=0)
        sizes = maxs - mins

        if approximate_large and len(vertices) > 50000:
            # Faster but approximate: bounding box diagonal.
            # Good for a first GigaPose run, but not exact BOP diameter.
            diameter = float(np.linalg.norm(sizes))
            print(
                f"Warning: using approximate diameter for {model_path.name} "
                f"because it has {len(vertices)} vertices."
            )
        else:
            diameter = compute_diameter_chunked(vertices)

        models_info[str(obj_id)] = {
            "diameter": diameter,
            "min_x": float(mins[0]),
            "min_y": float(mins[1]),
            "min_z": float(mins[2]),
            "size_x": float(sizes[0]),
            "size_y": float(sizes[1]),
            "size_z": float(sizes[2]),
        }

        print(f"Processed {model_path.name}: object id {obj_id}")

    return models_info


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models_dir",
        type=str,
        required=True,
        help="Path to BOP models folder containing obj_000001.ply, etc.",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help=(
            "Scale applied to vertices before computing info. "
            "Use 1.0 if your PLY is already in millimeters. "
            "Use 1000.0 if your PLY is in meters."
        ),
    )
    parser.add_argument(
        "--approximate_large",
        action="store_true",
        help="Use bounding-box diagonal as approximate diameter for very large meshes.",
    )
    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    output_path = models_dir / "models_info.json"

    models_info = compute_models_info(
        models_dir=models_dir,
        scale=args.scale,
        approximate_large=args.approximate_large,
    )

    with open(output_path, "w") as f:
        json.dump(models_info, f, indent=2)

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()