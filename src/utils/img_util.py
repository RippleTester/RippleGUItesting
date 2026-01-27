import base64
from pathlib import Path

import io
from typing import Union

import matplotlib.pyplot as plt
import pyautogui
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from supervision.detection.core import Detections

from src.pipelines.placeholder import Placeholder
from src.utils.box_annotator import BoxAnnotator
from supervision.draw.color import ColorPalette


class ImgUtil:

    # https://docs.anthropic.com/en/docs/build-with-claude/vision#evaluate-image-size
    """
    We do not recommend sending screenshots in resolutions above XGA/WXGA to avoid issues related to image resizing.
    Relying on the image resizing behavior in the API will result in lower model accuracy and slower performance than implementing scaling in your tools directly.
    When implementing computer use yourself, we recommend using XGA resolution (1024x768):
        For higher resolutions: Scale the image down to XGA and let the model interact with this scaled version, then map the coordinates back to the original resolution proportionally.
        For lower resolutions or smaller devices (e.g. mobile devices): Add black padding around the display area until it reaches 1024x768.
    """
    # Target resolutions (do not upscale above these sizes)
    MAX_SCALING_TARGETS: dict[str, dict] = {
        "XGA": {"width": 1024, "height": 768},  # 4:3
        # "WXGA": {"width": 1280, "height": 800},  # 16:10
        # "FWXGA": {"width": 1366, "height": 768},  # ~16:9
    }

    @staticmethod
    def choose_target_resolution(original_width: int, original_height: int) -> tuple[str, dict]:
        """
        Choose the best target resolution from MAX_SCALING_TARGETS that is not larger than the original.
        Among those, the one with an aspect ratio closest to the original is selected.
        Returns (target_name, target_dict).
        """
        orig_ratio = original_width / original_height
        best_target_name = None
        best_target = None
        min_diff = float('inf')
        for name, target in ImgUtil.MAX_SCALING_TARGETS.items():
            # Consider only targets that are smaller than or equal to the original dimensions.
            if target["width"] <= original_width and target["height"] <= original_height:
                target_ratio = target["width"] / target["height"]
                diff = abs(orig_ratio - target_ratio)
                if diff < min_diff:
                    min_diff = diff
                    best_target_name = name
                    best_target = target
        # If no target qualifies (i.e. image is smaller than all targets), default to XGA.
        if best_target is None:
            best_target_name = "XGA"
            best_target = ImgUtil.MAX_SCALING_TARGETS["XGA"]
        return best_target_name, best_target

    @staticmethod
    def convert_to_target_resolution(image_path: str):
        """
        Convert the input image to one of the target resolutions defined in MAX_SCALING_TARGETS.

        If the original image's aspect ratio is nearly equal to the target's (within a tolerance),
        the image is directly resized. Otherwise, black padding is added (to preserve proportions)
        and then the padded image is resized.

        Returns:
            final_img: The resulting image at the target resolution.
            transformation: A dictionary with details for mapping coordinates from the final image
                            back to the original. It includes:
                              - method: 'resize' or 'padding'
                              - For 'resize': {'scale_factor': (scale_x, scale_y)}
                              - For 'padding': {'padded_size': (padded_width, padded_height), 'padding': (pad_x, pad_y)}
                            In both cases, 'target_size': (target_width, target_height) is stored.
            original_size: Tuple (original_width, original_height)
        """
        img = Image.open(image_path)
        original_width, original_height = img.size
        orig_ratio = original_width / original_height

        target_name, target = ImgUtil.choose_target_resolution(original_width, original_height)
        target_width, target_height = target["width"], target["height"]
        target_ratio = target_width / target_height
        epsilon = 0.01

        if abs(orig_ratio - target_ratio) < epsilon:
            # Aspect ratios nearly match: direct resize.
            final_img = img.resize((target_width, target_height), Image.LANCZOS)
            scale_x = original_width / target_width
            scale_y = original_height / target_height
            transformation = {
                'method': 'resize',
                'scale_factor': (scale_x, scale_y),
                'target_size': (target_width, target_height),
                'original_size': (original_width, original_height)
            }
        else:
            # Aspect ratios differ: pad the image to match the target ratio.
            # Option 1: keep original width and compute padded height.
            padded_height_candidate = original_width / target_ratio
            if padded_height_candidate >= original_height:
                padded_width = original_width
                padded_height = int(round(padded_height_candidate))
            else:
                # Option 2: keep original height and compute padded width.
                padded_width_candidate = original_height * target_ratio
                padded_width = int(round(padded_width_candidate))
                padded_height = original_height

            # Compute padding offsets to center the original image.
            pad_x = (padded_width - original_width) // 2
            pad_y = (padded_height - original_height) // 2

            # Create a new black canvas and paste the original image.
            padded_img = Image.new("RGB", (padded_width, padded_height), (0, 0, 0))
            padded_img.paste(img, (pad_x, pad_y))

            # Resize the padded image to the target resolution.
            final_img = padded_img.resize((target_width, target_height), Image.LANCZOS)
            transformation = {
                'method': 'padding',
                'padded_size': (padded_width, padded_height),
                'padding': (pad_x, pad_y),
                'target_size': (target_width, target_height),
                'original_size': (original_width, original_height)
            }
        return final_img, transformation

    import pyautogui

    @staticmethod
    def scale_coordinates(final_coord: tuple[int, int], transformation: dict) -> tuple[int, int]:
        """
        Map a coordinate from the final (target) image back to the original image's logical coordinates.

        This function automatically calculates the DPI scale based on the original (physical) size
        of the screenshot and the logical screen size. The transformation dictionary is expected to contain
        the following keys:
            - 'target_size': (target_width, target_height)
            - 'original_size': (orig_width, orig_height)
            - 'method': either 'resize' or 'padding'
            - If method is 'resize': 'scale_factor': (scale_x, scale_y)
            - If method is 'padding': 'padded_size': (padded_width, padded_height) and 'padding': (pad_x, pad_y)

        Args:
            final_coord: (x, y) coordinate based on the final image (in physical pixels).
            transformation: A dictionary returned by convert_to_target() containing transformation details.

        Returns:
            (x, y) coordinate on the original image in logical pixels (as integers).
        """
        x, y = final_coord
        target_width, target_height = transformation['target_size']

        # Get the logical screen size (e.g., 1440x900)
        logical_width, logical_height = pyautogui.size()

        # Retrieve the original physical screenshot size (e.g., 2880x1800)
        orig_width, orig_height = transformation['original_size']

        # Calculate DPI scale (assumes uniform scaling factor, e.g., 2880/1440 = 2)
        dpi_scale = orig_width / logical_width

        if transformation['method'] == 'resize':
            scale_x, scale_y = transformation['scale_factor']
            orig_x = x * scale_x
            orig_y = y * scale_y
        elif transformation['method'] == 'padding':
            padded_width, padded_height = transformation['padded_size']
            pad_x, pad_y = transformation['padding']
            # First, map the coordinate from the final image back to the padded image coordinate system.
            padded_x = x * padded_width / target_width
            padded_y = y * padded_height / target_height
            # Then, subtract the padding offset to get the coordinate on the original image (in physical pixels).
            orig_x = padded_x - pad_x
            orig_y = padded_y - pad_y
        else:
            raise ValueError("Unknown transformation method.")

        # Convert the physical coordinate to a logical coordinate by dividing by the DPI scale.
        logical_x = int(orig_x / dpi_scale)
        logical_y = int(orig_y / dpi_scale)
        return logical_x, logical_y

    # @staticmethod
    # def encode_image(image_path, encoding='utf-8'):
    #     # Function to encode the image
    #     with open(image_path, "rb") as image_file:
    #         return base64.b64encode(image_file.read()).decode(encoding)

    @staticmethod
    def encode_image(image_path: Union[str, Image.Image], encoding='utf-8', format='PNG'):
        if isinstance(image_path, str):
            # 如果是路径，按原来的方式读取文件
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode(encoding)
        elif isinstance(image_path, Image.Image):
            # 如果是 PIL Image 对象，转换为 base64
            buffered = io.BytesIO()
            image_path.save(buffered, format=format)
            return base64.b64encode(buffered.getvalue()).decode(encoding)
        else:
            raise TypeError("Input must be a file path (str) or a PIL.Image.Image object")

    @staticmethod
    def decode_image(base64_image):
        # Decode the base64-encoded image string
        decoded_image = base64.b64decode(base64_image)

        # Open the image using PIL (Python Imaging Library)
        img = Image.open(io.BytesIO(decoded_image))

        # # Display the image
        # img.show()
        return img

    @staticmethod
    def check_image_resolution(img_path):
        with open(img_path, 'rb') as image_file:
            image = Image.open(image_file)
            width, height = image.size
            print(f"Original image resolution: {width}x{height}")

            # Encode the image in base64
            image_file.seek(0)
            base64_encoded = base64.b64encode(image_file.read()).decode('utf-8')

            # Decode the base64 string back to an image
            image_data = base64.b64decode(base64_encoded)
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            print(f"Decoded image resolution: {width}x{height}")

    @staticmethod
    def set_img_with_grid(img_path, img_name, figsize=(14.4, 9), gird_space=50):
        # Display the image
        img = Image.open(Path(img_path, f"{img_name}.png"))
        # Create a figure and an axes
        # Load the image and display it with a grid without changing its resolution
        fig, ax = plt.subplots(figsize=figsize)  # Adjust figure size to match image resolution
        # fig, ax = plt.subplots(figsize=(28.8, 18))  # Adjust figure size to match image resolution
        # fig, ax = plt.subplots()  # Adjust figure size to match image resolution

        # Display the image
        ax.imshow(img)
        ax.axis('on')

        # Add a grid
        xticks = range(0, img.width, gird_space)
        yticks = range(0, img.height, gird_space)
        ax.set_xticks(xticks)
        ax.set_yticks(yticks)
        ax.grid(color='gray', linestyle='--', linewidth=0.5)
        # Label the axes
        ax.set_xlabel('X Axis')
        ax.set_ylabel('Y Axis')
        # Annotate each grid point with its coordinates
        for x in xticks:
            for y in yticks:
                ax.text(x, y, f'({x},{y})', color='blue', fontsize=5.5, ha='center', va='center')

        # Save the image with grid
        grid_image_path = Path(img_path, f"{img_name}_with_grid.png")
        plt.savefig(grid_image_path, bbox_inches='tight', pad_inches=0, dpi=100)
        plt.show()
        fig.savefig(Path(img_path, f"{img_name}_with_grid.png"))

    @staticmethod
    def calculate_coordinate_by_num(image_path, number, interval=100):
        # Load the image to get its dimensions
        image = Image.open(image_path)
        width, height = image.size

        # Calculate the number of columns
        columns = width // interval

        # Calculate row and column indices for the given number
        row_index = (number - 1) // columns
        column_index = (number - 1) % columns

        # Calculate the coordinates
        x_coordinate = column_index * interval
        y_coordinate = row_index * interval
        return (x_coordinate, y_coordinate)

    @staticmethod
    def set_img_with_nums(img_path, img_name, interval=50, font_size=12, font_color="red"):
        # Load the uploaded image
        image = Image.open(Path(img_path, f"{img_name}.png"))
        draw = ImageDraw.Draw(image)

        # Define font size and font for numbering
        try:
            font_path = "/Library/Fonts/Arial.ttf"
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            font = ImageFont.load_default()
            print("Could not load specified font. Using default font.")

        # Get image dimensions
        width, height = image.size

        # Dictionary to store number and coordinate relationships
        num_coord_dict = {}

        # Draw the numbers and store coordinates
        number = 1
        for y in range(0, height, interval):
            for x in range(0, width, interval):
                draw.text((x, y), str(number), fill=font_color, font=font)
                num_coord_dict[number] = (x, y)
                number += 1

        # Save the modified image
        final_image_path_new = Path(img_path, f"{img_name}_with_nums.png")
        image.save(final_image_path_new)

        # Return the modified image and the dictionary
        return image, num_coord_dict

    @staticmethod
    def cover_top_bar_with_black_padding(image_path, output_path, top_bar_height=25):
        """
        Covers the top bar of an image with black padding.

        Parameters:
            image_path (str): Path to the input image.
            output_path (str): Path to save the modified image.
            top_bar_height (int): Height of the top bar to be covered in pixels. Default is 40.
        """
        # Load the image
        image = Image.open(image_path)

        # Create a drawing context
        draw = ImageDraw.Draw(image)

        # Draw a black rectangle over the top bar
        draw.rectangle([0, 0, image.width, top_bar_height], fill="black")

        # Save the modified image
        image.save(output_path)


    @staticmethod
    def draw_bounding_boxes(img_dir, img_name, element_list):
        # -------------------------------
        # 1. 读入原始图像
        # -------------------------------
        img = cv2.imread(Path(img_dir, f"{img_name}"))
        h, w = img.shape[:2]

        # -------------------------------
        # 2. 如果 element_list 为空，直接返回原图
        # -------------------------------
        if not element_list:
            annotated_img_filepath = Path(img_dir, f'{Placeholder.PARSED_}{img_name}')
            cv2.imwrite(annotated_img_filepath, img)  # 保存原图为“标注图”
            print(f"[INFO] No elements to annotate for {img_name}. Saved original image.")
            return str(annotated_img_filepath), []

        # -------------------------------
        # 3. 把 bbox 转为像素坐标，收集 label
        # -------------------------------
        abs_boxes = []
        labels = []
        for item in element_list:
            x1, y1, x2, y2 = item['bbox']
            abs_boxes.append([x1, y1, x2, y2])
            item['bbox'] = [x1, y1, x2, y2]
            labels.append(f"{item[Placeholder.NO]}")

        abs_boxes = np.array(abs_boxes, dtype=int)

        # -------------------------------
        # 4. 构造 Detections
        # -------------------------------
        confs = np.ones(len(abs_boxes))
        class_ids = np.array([item[Placeholder.NO] for item in element_list])

        detections = Detections(
            xyxy=abs_boxes,
            confidence=confs,
            class_id=class_ids
        )

        # -------------------------------
        # 5. 调用 BoxAnnotator
        # -------------------------------
        box_annotator = BoxAnnotator(
            color=ColorPalette.DEFAULT,
            thickness=1,
            text_scale=0.3,
            text_thickness=1,
            text_padding=4,
            avoid_overlap=True
        )

        annotated_img = box_annotator.annotate(
            scene=img.copy(),
            detections=detections,
            labels=labels,
            skip_label=False,
            image_size=(w, h)
        )

        # -------------------------------
        # 6. 保存标注图
        # -------------------------------
        annotated_img_filepath = Path(img_dir, f'{Placeholder.PARSED_}{img_name}')
        cv2.imwrite(annotated_img_filepath, annotated_img)

        return str(annotated_img_filepath), element_list

    @staticmethod
    def detect_image_differences_by_pixel(
            img1_path,
            img2_path,
            threshold=30,
            dilation_kernel=(5, 5),
            dilation_iterations=2
    ):
        """
        Compare two images and return numbered bounding boxes of regions where they differ,
        outputting coordinates as [x1, y1, x2, y2].

        Parameters:
            img1_path (str or Path): Path to the first image.
            img2_path (str or Path): Path to the second image.
            threshold (int): Pixel-difference threshold for change detection.
            dilation_kernel (tuple): Kernel size for dilation to merge nearby changes.
            dilation_iterations (int): Number of dilation iterations.

        Returns:
            List[dict]: A list of dicts, each with:
                'no'   : int index starting from 0,
                'bbox' : [x1, y1, x2, y2] coordinates of the region.
        """
        # Load images
        img1 = cv2.imread(str(img1_path))
        img2 = cv2.imread(str(img2_path))
        if img1 is None or img2 is None:
            raise FileNotFoundError("Could not load one of the images.")
        if img1.shape != img2.shape:
            raise ValueError("Images must have the same dimensions.")

        # Compute difference mask
        diff = cv2.absdiff(img1, img2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, bin_mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

        # Dilate mask to connect nearby differences
        kernel = np.ones(dilation_kernel, np.uint8)
        dilated = cv2.dilate(bin_mask, kernel, iterations=dilation_iterations)

        # Find contours and extract boxes
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[:2])

        # Build numbered boxes list
        results = []
        for idx, cnt in enumerate(contours, start=0):
            x, y, w, h = cv2.boundingRect(cnt)
            x1, y1 = x, y
            x2, y2 = x + w, y + h
            results.append({'no': idx, 'bbox': [x1, y1, x2, y2]})

        return results
