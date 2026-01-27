from pathlib import Path

import pyautogui
import time
from src.pipelines.placeholder import Placeholder
from src.utils.img_util import ImgUtil


class PyautoguiUtil:
    @staticmethod
    def capture_screenshot(save_path):
        """
        Captures the entire screen and saves the image to the given path.
        """
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(save_path)
            print(f"Screenshot saved to {save_path}")
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None

    @staticmethod
    def click(x, y):
        """
        Performs a single left-click at the specified (x, y) coordinates.
        """
        try:
            pyautogui.click(x, y, clicks=1)  # Setting the clicks parameter to 2 within the click() function will make the chrome browser just opened the active window and the second click will click the link at the coordinates entered in the click() function.
            print(f"Clicked at ({x}, {y})")
        except Exception as e:
            print(f"Error clicking at ({x}, {y}): {e}")

    @staticmethod
    def double_click(x, y):
        """
        Performs a double-click at the specified (x, y) coordinates.
        """
        try:
            pyautogui.doubleClick(x, y)
            print(f"Double clicked at ({x}, {y})")
        except Exception as e:
            print(f"Error double clicking at ({x}, {y}): {e}")

    @staticmethod
    def right_click(x, y):
        """
        Performs a right-click at the specified (x, y) coordinates.
        """
        try:
            pyautogui.rightClick(x, y)
            print(f"Right clicked at ({x}, {y})")
        except Exception as e:
            print(f"Error right clicking at ({x}, {y}): {e}")

    @staticmethod
    def type_text(text, interval=0.1):
        """
        Types the given text with an optional delay between each key press.
        """
        try:
            pyautogui.write(text, interval=interval)
            print(f"Typed text: {text}")
        except Exception as e:
            print(f"Error typing text '{text}': {e}")

    @staticmethod
    def long_press(x, y, duration=2):
        """
        Performs a long press (mouse down, wait, mouse up) at the specified coordinates.
        Duration is in seconds.
        """
        try:
            pyautogui.mouseDown(x, y)
            time.sleep(duration)
            pyautogui.mouseUp(x, y)
            print(f"Long pressed at ({x}, {y}) for {duration} seconds")
        except Exception as e:
            print(f"Error performing long press at ({x}, {y}): {e}")

    @staticmethod
    def move_mouse(x, y, duration=1):
        """
        Moves the mouse pointer to the specified (x, y) coordinates over a given duration.
        """
        try:
            pyautogui.moveTo(x, y, duration=duration)
            print(f"Moved mouse to ({x}, {y}) over {duration} seconds")
        except Exception as e:
            print(f"Error moving mouse to ({x}, {y}): {e}")

    @staticmethod
    def scroll(amount):
        """
        Scrolls the mouse wheel. Positive values scroll up; negative values scroll down.
        """
        try:
            pyautogui.scroll(amount)
            print(f"Scrolled {amount}")
        except Exception as e:
            print(f"Error scrolling: {e}")

    @staticmethod
    def hotkey(*args):
        """
        @todo
        Presses a combination of keys.
        """
        try:
            # In macOS, press command key first before any key for the hotkey, so add interval between them.
            pyautogui.hotkey(*args, interval=0.1)
            print(f"Pressed hotkey combination: {args}")
        except Exception as e:
            print(f"Error pressing hotkey combination {args}: {e}")

    @staticmethod
    def drag_and_drop(start, end, duration=1):
        """
        Drags the mouse from the start point to the end point over a given duration.

        :param start: Tuple (x, y) for the starting position.
        :param end: Tuple (x, y) for the ending position.
        :param duration: Time in seconds for the drag.
        """
        try:
            pyautogui.moveTo(start[0], start[1])
            pyautogui.dragTo(end[0], end[1], duration=duration, button='left')
            print(f"Dragged from {start} to {end} over {duration} seconds.")
        except Exception as e:
            print(f"Error dragging from {start} to {end}: {e}")

    @staticmethod
    def move_relative(dx, dy, duration=0.5):
        """
        Moves the mouse relative to its current position.

        :param dx: Change in x-coordinate.
        :param dy: Change in y-coordinate.
        :param duration: Time in seconds for the movement.
        """
        try:
            pyautogui.moveRel(dx, dy, duration=duration)
            print(f"Moved mouse relatively by ({dx}, {dy}) over {duration} seconds.")
        except Exception as e:
            print(f"Error moving mouse relatively by ({dx}, {dy}): {e}")

    @staticmethod
    def capture_region_screenshot(region, save_path):
        """
        Captures a screenshot of a specific region and saves it.

        :param region: A tuple (left, top, width, height) specifying the region.
        :param save_path: Path to save the screenshot.
        """
        try:
            screenshot = pyautogui.screenshot(region=region)
            screenshot.save(save_path)
            print(f"Region screenshot saved to {save_path}")
        except Exception as e:
            print(f"Error capturing region screenshot {region}: {e}")

    @staticmethod
    def locate_on_screen(image_path, confidence=0.9):
        """
        Searches for the given image on the screen and returns its coordinates.

        :param image_path: The file path of the image to search for.
        :param confidence: Matching confidence (requires opencv-python for improved accuracy).
        :return: A Box (left, top, width, height) if found; None otherwise.
        """
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                print(f"Found image at {location}")
                return location
            else:
                print("Image not found on screen.")
                return None
        except Exception as e:
            print(f"Error locating image on screen: {e}")
            return None

    @staticmethod
    def show_alert(message, title="Alert"):
        """
        Displays an alert dialog with the given message.

        :param message: The message to display.
        :param title: The title of the alert dialog.
        """
        try:
            pyautogui.alert(text=message, title=title)
        except Exception as e:
            print(f"Error showing alert: {e}")

    @staticmethod
    def ask_confirmation(message, title="Confirm"):
        """
        Displays a confirmation dialog and returns True if OK is pressed.

        :param message: The message to display.
        :param title: The title of the dialog.
        :return: True if confirmed; False otherwise.
        """
        try:
            result = pyautogui.confirm(text=message, title=title, buttons=["OK", "Cancel"])
            return result == "OK"
        except Exception as e:
            print(f"Error asking for confirmation: {e}")
            return False

    @staticmethod
    def get_mouse_position():
        """
        Returns the current position of the mouse cursor.
        """
        try:
            pos = pyautogui.position()
            print(f"Current mouse position: {pos}")
            return pos
        except Exception as e:
            print(f"Error getting mouse position: {e}")
            return None

    @staticmethod
    def execute(action, coordinate=None, input_text=None, scroll_direction=None, extra=None):
        """
        Executes an action defined by the Placeholder.

        Parameters:
            action: The action to perform (e.g., Placeholder.TAP, Placeholder.INPUT, etc.).
            coordinate: Tuple (x, y) for actions requiring a position. For actions like DRAG_AND_DROP,
                        coordinate should be a tuple of two tuples: ((start_x, start_y), (end_x, end_y)).
                        For MOVE_RELATIVE, coordinate should be (dx, dy).
            input_text: The text to type (for Placeholder.INPUT).
            scroll_direction: Direction for scrolling ('up' or 'down').
            extra: A dictionary for any extra parameters needed by certain actions.
                   For example, for CAPTURE_REGION: {'region': (left, top, width, height), 'save_path': path}
                   For LOCATE: {'image_path': path, 'confidence': value}
                   For ALERT or CONFIRM: {'message': str, 'title': str (optional)}
        """

        try:
            if action == Placeholder.TAP or action == Placeholder.CLICK:
                if coordinate is None:
                    raise ValueError("Coordinate required for TAP action")
                PyautoguiUtil.click(coordinate[0], coordinate[1])

            elif action == Placeholder.RIGHT_TAP:  # New branch for right-click
                if coordinate is None:
                    raise ValueError("Coordinate required for RIGHT_CLICK action")
                PyautoguiUtil.right_click(coordinate[0], coordinate[1])

            elif action == Placeholder.LONG_TAP:
                if coordinate is None:
                    raise ValueError("Coordinate required for LONG_TAP action")
                PyautoguiUtil.long_press(coordinate[0], coordinate[1])

            elif action == Placeholder.DOUBLE_TAP:
                if coordinate is None:
                    raise ValueError("Coordinate required for DOUBLE_TAP action")
                PyautoguiUtil.double_click(coordinate[0], coordinate[1])

            elif action == Placeholder.INPUT:
                if coordinate is None or input_text is None:
                    raise ValueError("Coordinate and input_text required for INPUT action")
                PyautoguiUtil.click(coordinate[0], coordinate[1])
                time.sleep(0.5)  # Short delay to ensure focus
                PyautoguiUtil.type_text(input_text)

            elif action == Placeholder.SCROLL:
                if scroll_direction is None:
                    raise ValueError("Scroll direction required for SCROLL action")
                if scroll_direction.lower() == 'up':
                    PyautoguiUtil.scroll(500)
                elif scroll_direction.lower() == 'down':
                    PyautoguiUtil.scroll(-500)
                else:
                    raise ValueError("Invalid scroll_direction; use 'up' or 'down'.")

            elif action == Placeholder.HOME:
                # Example: On Windows, using the Windows key.
                PyautoguiUtil.hotkey('winleft')

            elif action == Placeholder.ENTER:
                PyautoguiUtil.hotkey('enter')

            # Additional new actions:
            elif action == Placeholder.DRAG_AND_DROP:
                # Expect coordinate to be ((start_x, start_y), (end_x, end_y))
                if coordinate is None or not (isinstance(coordinate, tuple) and len(coordinate) == 2):
                    raise ValueError("Coordinate must be a tuple of two tuples for DRAG_AND_DROP action")
                PyautoguiUtil.drag_and_drop(coordinate[0], coordinate[1])

            elif action == Placeholder.MOVE_RELATIVE:
                # Expect coordinate to be (dx, dy)
                if coordinate is None or not (isinstance(coordinate, tuple) and len(coordinate) == 2):
                    raise ValueError("Coordinate must be a tuple (dx, dy) for MOVE_RELATIVE action")
                PyautoguiUtil.move_relative(coordinate[0], coordinate[1])

            elif action == Placeholder.CAPTURE_REGION:
                # extra must include keys: 'region' and 'save_path'
                if extra is None or 'region' not in extra or 'save_path' not in extra:
                    raise ValueError("For CAPTURE_REGION, extra must include 'region' and 'save_path'")
                PyautoguiUtil.capture_region_screenshot(extra['region'], extra['save_path'])

            elif action == Placeholder.LOCATE:
                # extra must include key: 'image_path'; 'confidence' is optional.
                if extra is None or 'image_path' not in extra:
                    raise ValueError("For LOCATE, extra must include 'image_path'")
                location = PyautoguiUtil.locate_on_screen(extra['image_path'], extra.get('confidence', 0.9))
                print(f"Location found: {location}")

            elif action == Placeholder.ALERT:
                # extra must include key: 'message'; 'title' is optional.
                if extra is None or 'message' not in extra:
                    raise ValueError("For ALERT, extra must include 'message'")
                PyautoguiUtil.show_alert(extra['message'], extra.get('title', "Alert"))

            elif action == Placeholder.CONFIRM:
                # extra must include key: 'message'; 'title' is optional.
                if extra is None or 'message' not in extra:
                    raise ValueError("For CONFIRM, extra must include 'message'")
                confirmed = PyautoguiUtil.ask_confirmation(extra['message'], extra.get('title', "Confirm"))
                print(f"Confirmation result: {confirmed}")

            elif action == Placeholder.GET_MOUSE_POSITION:
                pos = PyautoguiUtil.get_mouse_position()
                print(f"Current mouse position: {pos}")

            else:
                print(f"Invalid action: {action}")

            time.sleep(2)  # Delay after performing the action for stability

        except Exception as e:
            print(f"Error executing action {action}: {e}")

    @staticmethod
    def launch_app(app_keyword='firefox'):
        """
        launch the app
        """
        # Open Spotlight using Command + Space
        # In macOS, press command key first before any key for the hotkey, so add interval between them.
        # interval not too long, since 'Hold Command + Space' is Siri
        pyautogui.hotkey('command', 'space', interval=0.1)
        # Type the application name (e.g., TextEdit)
        pyautogui.write(app_keyword)
        # three different ways for enter
        # pyautogui.press('enter', presses=2)
        # pyautogui.write('\n')
        pyautogui.hotkey('enter', interval=0.1)

    @staticmethod
    def capture_and_process_screenshot(app_directory, screenshot_name,
                                       with_image_scale=True
                                       # region_coords=(0,0,1024,768)
                                       ):
        """
        region_coords = (left, top, width, height)

        """
        #
        resized_img_details = None
        # time.sleep(0.5)
        screenshot_filepath = Path(app_directory, f"{screenshot_name}.png")
        # PyautoguiUtil.capture_region_screenshot(region_coords, str(screenshot_filepath))
        PyautoguiUtil.capture_screenshot(str(screenshot_filepath))
        if with_image_scale:
            resized_img, resized_img_details = ImgUtil.convert_to_target_resolution(str(screenshot_filepath))
            # print(resized_img)
            print(resized_img_details)
            resized_screenshot_filepath = Path(app_directory, f"{screenshot_name}_{Placeholder.SCALE}.png")
            resized_img.save(Path(resized_screenshot_filepath))
            screenshot_filepath = resized_screenshot_filepath
            ImgUtil.check_image_resolution(screenshot_filepath)
            # print(screenshot_filepath)
        base64_image = ImgUtil.encode_image(screenshot_filepath)
        # return base64_image, screenshot_filepath

        return base64_image, screenshot_filepath, resized_img_details

    # @staticmethod
    # def capture_and_process_screenshot(app_directory, screenshot_name,
    #                                    with_image_scale=True
    #                                    # , region_coords=(0,0,1024,768)
    #                                    ):
    #     """
    #     region_coords = (left, top, width, height)
    #
    #     """
    #     #
    #     resized_img_details = None
    #     # time.sleep(0.5)
    #     screenshot_filepath = Path(app_directory, f"{screenshot_name}.png")
    #     # PyautoguiUtil.capture_region_screenshot(region_coords, str(screenshot_filepath))
    #     PyautoguiUtil.capture_screenshot(str(screenshot_filepath))
    #     if with_image_scale:
    #         resized_img, resized_img_details, _ = ImgUtil.convert_to_target(str(screenshot_filepath))
    #         # print(resized_img)
    #         # print(resized_img_details)
    #         resized_screenshot_filepath = Path(app_directory, f"resized_{screenshot_name}.png")
    #         resized_img.save(Path(resized_screenshot_filepath))
    #         screenshot_filepath = resized_screenshot_filepath
    #         ImgUtil.check_image_resolution(screenshot_filepath)
    #         # print(screenshot_filepath)
    #     base64_image = ImgUtil.encode_image(screenshot_filepath)
    #     return base64_image, screenshot_filepath, resized_img_details


