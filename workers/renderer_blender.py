import bpy
import sys
import os
import json
import logging

# Basic logging setup for the worker
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def apply_render_profile(profile: dict):
    """Applies rendering settings from a profile dictionary to the current scene."""
    scene = bpy.context.scene
    logging.info(f"Applying render profile: {profile}")

    if 'resolution' in profile and len(profile['resolution']) == 2:
        scene.render.resolution_x = profile['resolution'][0]
        scene.render.resolution_y = profile['resolution'][1]
        logging.info(f"  - Set resolution to {scene.render.resolution_x}x{scene.render.resolution_y}")

    if 'engine' in profile:
        scene.render.engine = profile['engine']
        logging.info(f"  - Set engine to {scene.render.engine}")

    if scene.render.engine == 'CYCLES':
        if 'samples' in profile:
            scene.cycles.samples = int(profile['samples'])
            logging.info(f"  - Set Cycles samples to {scene.cycles.samples}")
        if 'denoise' in profile and profile['denoise']:
            scene.cycles.use_denoising = True
            logging.info(f"  - Enabled Cycles denoising")
        if 'device' in profile:
            scene.cycles.device = profile['device']
            logging.info(f"  - Set Cycles device to {scene.cycles.device}")

    elif scene.render.engine == 'EEVEE':
        if 'samples' in profile:
            scene.eevee.taa_render_samples = int(profile['samples'])
            logging.info(f"  - Set Eevee samples to {scene.eevee.taa_render_samples}")

def render_scene(input_path: str, output_path: str, profile_json: str):
    """
    Imports an OBJ file, configures the scene based on a profile, and renders it.
    """
    logging.info("--- Blender Rendering Worker ---")
    logging.info(f"Input OBJ: {input_path}")
    logging.info(f"Output PNG: {output_path}")

    try:
        profile = json.loads(profile_json)

        # --- 1. Scene Setup ---
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        # --- 2. Import the OBJ file ---
        logging.info(f"Importing OBJ file from {input_path}...")
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input OBJ file not found at {input_path}")
        bpy.ops.import_scene.obj(filepath=input_path)
        imported_object = bpy.context.selected_objects[0]
        logging.info("OBJ file imported successfully.")

        # --- 3. Camera and Light Setup ---
        bpy.ops.object.camera_add(location=(7, -7, 5))
        camera = bpy.context.active_object
        camera_constraint = camera.constraints.new(type='TRACK_TO')
        camera_constraint.target = imported_object
        bpy.ops.object.light_add(type='SUN', location=(10, 10, 10), energy=3.0)

        # --- 4. Apply Profile and Render ---
        scene = bpy.context.scene
        scene.camera = camera
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = output_path

        apply_render_profile(profile)

        logging.info("Starting render...")
        bpy.ops.render.render(write_still=True)
        logging.info(f"Render complete! Image saved to {output_path}")
        print(f"Success: Rendered image saved to {output_path}")

    except Exception as e:
        logging.error(f"An error occurred during rendering: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        argv = sys.argv
        if "--" not in argv:
            raise IndexError("Missing script arguments.")

        args = argv[argv.index("--") + 1:]
        if len(args) < 3:
            raise IndexError("Not enough arguments. Requires input_obj_path, output_png_path, and profile_json.")

        input_file_arg = args[0]
        output_file_arg = args[1]
        profile_json_arg = args[2]

        output_dir = os.path.dirname(output_file_arg)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        render_scene(input_file_arg, output_file_arg, profile_json_arg)

    except Exception as e:
        logging.error(f"Argument parsing or execution failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        print("Usage: blender --background --python renderer_blender.py -- <in.obj> <out.png> '{{...}}'", file=sys.stderr)
        sys.exit(1)