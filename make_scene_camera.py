import argparse
import json
from pathlib import Path


CAM_K = [
    3359.606641322341, 0.0, 2110.844067989589,
    0.0, 3341.5393430371087, 1085.0067301430872,
    0.0, 0.0, 1.0,
]


def get_image_id(image_path: Path) -> int:
    """
    Convert BOP image filename to image id.

    Example:
        000000.png -> 0
        000123.jpg -> 123
    """
    return str(image_path.stem)


def write_scene_camera(scene_dir: Path, depth_scale: float = 1.0):
    rgb_dir = scene_dir / "rgb"

    if not rgb_dir.exists():
        print(f"Skipping {scene_dir}: no rgb/ folder")
        return

    image_paths = sorted(
        list(rgb_dir.glob("*.png")) +
        list(rgb_dir.glob("*.jpg")) +
        list(rgb_dir.glob("*.jpeg"))
    )

    if not image_paths:
        print(f"Skipping {scene_dir}: no RGB images found")
        return

    scene_camera = {}

    for image_path in image_paths:
        image_id = get_image_id(image_path)

        scene_camera[str(image_id)] = {
            "cam_K": CAM_K,
            "depth_scale": depth_scale,
        }

    output_path = scene_dir / "scene_camera.json"

    with open(output_path, "w") as f:
        json.dump(scene_camera, f, indent=2)

    print(f"Saved {output_path} with {len(image_paths)} images")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test_dir",
        type=str,
        required=True,
        help="Path to BOP test folder, e.g. /path/to/mybop/test",
    )
    parser.add_argument(
        "--depth_scale",
        type=float,
        default=1.0,
        help="Depth scale value. Use 1.0 for RGB-only custom data.",
    )

    args = parser.parse_args()

    test_dir = Path(args.test_dir)

    if not test_dir.exists():
        raise FileNotFoundError(f"test_dir does not exist: {test_dir}")

    scene_dirs = sorted([p for p in test_dir.iterdir() if p.is_dir()])

    if not scene_dirs:
        raise FileNotFoundError(f"No scene folders found in {test_dir}")

    for scene_dir in scene_dirs:
        write_scene_camera(scene_dir, depth_scale=args.depth_scale)


if __name__ == "__main__":
    main()