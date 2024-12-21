import torch

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "comfy"))

import folder_paths

class SaveImageARGB16PNG:
    def __init__(self):
        import os
        import json
        try:
            from PIL import Image
            self.Image = Image
        except ImportError:
            raise ImportError("Pillow module not found. Please install it to save PNG images.")

        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "ComfyUI"})
            },
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "savepng"
    OUTPUT_NODE = True
    CATEGORY = "Marigold"

    def savepng(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        import numpy as np
        import os
        import re
        from PIL.PngImagePlugin import PngInfo

        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )
        results = []

        for batch_number, image in enumerate(images):
            image_np = image.cpu().numpy()
            image_np = (image_np * 65535).astype(np.uint16)  # Scale to 16-bit range

            if image_np.shape[-1] == 4:
                mode = "RGBA"
            else:
                mode = "RGB"

            image_pil = self.Image.fromarray(image_np, mode=mode)

            metadata = PngInfo()
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.png"

            image_pil.save(os.path.join(full_output_folder, file), format="PNG", compress_level=self.compress_level, pnginfo=metadata)

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1

        return { "ui": { "images": results } }


NODE_CLASS_MAPPINGS = {
    "SaveImageARGB16PNG": SaveImageARGB16PNG
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageARGB16PNG": "SaveImageARGB16PNG"
}
