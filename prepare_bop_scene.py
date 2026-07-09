import argparse
import json
import shutil
from pathlib import Path


CAM_K = [
    3359.606641322341, 0.0, 2110.844067989589,
    0.0, 3341.5393430371087, 1085.0067301430872,
    0.0, 0.0, 1.0,
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_rgb_dir",
        required=True,
        help="Folder containing your original RGB images with any filenames.",
    )
    parser.add_argument(
        "--scene_dir",
        required=True,
        help="Output BOP scene folder, e.g. /path/to/mybop/test/000000",
    )
    parser.add_argument(
        "--depth_scale",
        type=float,
        default=1.0,
        help="Use 1.0 for RGB-only data.",
    )
    args = parser.parse_args()

    input_rgb_dir = Path(args.input_rgb_dir)
    scene_dir = Path(args.scene_dir)
    output_rgb_dir = scene_dir / "rgb"

    output_rgb_dir.mkdir(parents=True, exist_ok=True)

    image_paths = sorted(
        list(input_rgb_dir.glob("*.png")) +
        list(input_rgb_dir.glob("*.jpg")) +
        list(input_rgb_dir.glob("*.jpeg"))
    )

    if not image_paths:
        raise FileNotFoundError(f"No images found in {input_rgb_dir}")

    scene_camera = {}
    mapping = []

    for new_id, old_path in enumerate(image_paths):
        new_name = f"{new_id:06d}{old_path.suffix.lower()}"
        new_path = output_rgb_dir / new_name

        shutil.copy2(old_path, new_path)

        scene_camera[str(new_id)] = {
            "cam_K": CAM_K,
            "depth_scale": args.depth_scale,
        }

        mapping.append({
            "old_filename": old_path.name,
            "new_filename": new_name,
            "scene_id": int(scene_dir.name),
            "image_id": new_id,
        })

    with open(scene_dir / "scene_camera.json", "w") as f:
        json.dump(scene_camera, f, indent=2)

    with open(scene_dir / "image_name_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2)

    print(f"Saved RGB images to: {output_rgb_dir}")
    print(f"Saved scene camera to: {scene_dir / 'scene_camera.json'}")
    print(f"Saved mapping to: {scene_dir / 'image_name_mapping.json'}")
    print(f"Prepared {len(image_paths)} images")


if __name__ == "__main__":
    main()