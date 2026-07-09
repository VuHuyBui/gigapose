import argparse
from pathlib import Path

import trimesh


def scale_model(input_path: Path, output_path: Path, scale: float):
    mesh = trimesh.load(input_path, force="mesh", process=False)

    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(list(mesh.geometry.values()))

    mesh.vertices *= scale
    mesh.export(output_path)

    print(f"Saved scaled model:")
    print(f"  input : {input_path}")
    print(f"  output: {output_path}")
    print(f"  scale : {scale}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input .ply file")
    parser.add_argument("--output", required=True, help="Output .ply file")
    parser.add_argument(
        "--scale",
        type=float,
        default=1000.0,
        help="Use 1000 for meters to millimeters, 10 for centimeters to millimeters",
    )
    args = parser.parse_args()

    scale_model(
        input_path=Path(args.input),
        output_path=Path(args.output),
        scale=args.scale,
    )


if __name__ == "__main__":
    main()