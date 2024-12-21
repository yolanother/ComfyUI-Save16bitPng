import os
import sys
import json
import folder_paths

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "comfy"))


class SaveImageARGB16PNG:
    """
    A custom node for saving images in ARGB16 PNG format.

    This node saves images with high-quality 16-bit precision and supports metadata embedding.
    """
    def __init__(self):
        """
        Initializes the SaveImageARGB16PNG class.

        Attempts to import the Pillow library for image handling. Sets up default parameters
        like output directory and compression level.

        Raises:
            ImportError: If the Pillow library is not installed.
        """
        try:
            from PIL import Image
            self.Image = Image
        except ImportError:
            raise ImportError("Pillow module not found. Please install it to save PNG images.")

        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 0

    @classmethod
    def INPUT_TYPES(cls):
        """
        Defines the input types required by the node.

        Returns:
            dict: A dictionary containing required and hidden inputs for the node.
        """
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "ComfyUI"})
            },
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ()  # Specifies the return type of the node.
    FUNCTION = "savepng"  # Defines the main function to execute.
    OUTPUT_NODE = True  # Indicates this is an output node.
    CATEGORY = "image"  # Specifies the category of the node.

    def savepng(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        """
        Saves images in ARGB16 PNG format with optional metadata.

        Args:
            images (list): List of image tensors to be saved.
            filename_prefix (str): Prefix for the output filenames.
            prompt (str, optional): Metadata prompt to embed in the PNG files.
            extra_pnginfo (dict, optional): Additional metadata as key-value pairs to embed in the PNG files.

        Returns:
            dict: A dictionary with UI-compatible information about the saved images.
        """
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
            # Convert the image tensor to a numpy array and scale to 16-bit range.
            image_np = image.cpu().numpy()
            image_np = (image_np * 65535).astype(np.uint16)

            # Determine the image mode based on the number of channels.
            if image_np.shape[-1] == 4:
                mode = "RGBA"
            else:
                mode = "RGB"

            # Create a PIL Image object.
            image_pil = self.Image.fromarray(image_np, mode=mode)

            # Add metadata to the PNG if provided.
            metadata = PngInfo()
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            # Generate the output filename.
            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.png"

            # Save the image with metadata and specified compression level.
            image_pil.save(os.path.join(full_output_folder, file), format="PNG", compress_level=self.compress_level, pnginfo=metadata)

            # Append file information to the results.
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
