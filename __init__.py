import os
import sys
import folder_paths
import numpy as np
import re
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "comfy"))


class SaveImageARGB16PNG:
    def __init__(self):
        try:
            import OpenEXR
            import Imath
            self.OpenEXR = OpenEXR
            self.Imath = Imath
            self.use_openexr = True
        except ImportError:
            print("No OpenEXR module found, trying OpenCV...")
            self.use_openexr = False
            try:
                os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
                import cv2
                self.cv2 = cv2
            except ImportError:
                raise ImportError("No OpenEXR or OpenCV module found, can't save EXR")

        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "The images to save."}),
                "filename_prefix": ("STRING", {"default": "ComfyUI_EXR", "tooltip": "The prefix for the file to save. This may include formatting information such as %date:yyyy-MM-dd% or %Empty Latent Image.width% to include values from nodes."})
            },
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images_exr"

    OUTPUT_NODE = True

    CATEGORY = "image"
    DESCRIPTION = "Saves the input images as EXR files in your ComfyUI output directory."

    def save_images_exr(self, images, filename_prefix="ComfyUI_EXR", prompt=None, extra_pnginfo=None):
        from io import BytesIO
        from PIL import Image
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )
        results = list()

        def file_counter():
            max_counter = 0
            for existing_file in os.listdir(full_output_folder):
                match = re.fullmatch(f"{filename}_(\d+)_?\.[a-zA-Z0-9]+", existing_file)
                if match:
                    file_counter = int(match.group(1))
                    if file_counter > max_counter:
                        max_counter = file_counter
            return max_counter

        for (batch_number, image) in enumerate(images):
            image_np = image.cpu().numpy()
            image_np = image_np.astype(np.float32)

            if self.use_openexr:
                PIXEL_TYPE = self.Imath.PixelType(self.Imath.PixelType.FLOAT)
                height, width, channels = image_np.shape

                header = self.OpenEXR.Header(width, height)
                half_chan = self.Imath.Channel(PIXEL_TYPE)
                header['channels'] = dict([(c, half_chan) for c in "RGB"])

                R = image_np[:, :, 0].tobytes()
                G = image_np[:, :, 1].tobytes()
                B = image_np[:, :, 2].tobytes()

                counter = file_counter() + 1
                filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
                file = f"{filename_with_batch_num}_{counter:05}.png"

                with tempfile.NamedTemporaryFile(suffix=".exr", delete=True) as temp_exr_file:
                    # Create the EXR file using the temporary file
                    exr_file = self.OpenEXR.OutputFile(temp_exr_file.name, header)
                    exr_file.writePixels({'R': R, 'G': G, 'B': B})
                    exr_file.close()

                    # Open the temporary EXR file for conversion
                    img = Image.open(temp_exr_file.name)
                    img = img.convert("RGBA")
                    img.save(os.path.join(full_output_folder, file), format="PNG", bits=16)
            else:
                counter = file_counter() + 1
                filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
                file = f"{filename_with_batch_num}_{counter:05}.png"

                # Convert image to RGBA16 PNG and save using OpenCV
                image_rgba16 = (image_np * 65535).astype('uint16')
                rgba_image = self.cv2.merge((
                    image_rgba16[:, :, 0],
                    image_rgba16[:, :, 1],
                    image_rgba16[:, :, 2],
                    (image_rgba16[:, :, 0] * 0).astype('uint16') + 65535
                ))  # Add alpha channel with max value
                self.cv2.imwrite(os.path.join(full_output_folder, file), rgba_image)

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
    "SaveImageARGB16PNG": "Save Image RGBA 16 PNG",
}
