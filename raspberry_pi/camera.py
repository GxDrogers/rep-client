import time
import os
import logging
from picamera import PiCamera

# Configure logging
logger = logging.getLogger("Camera")

# Create directory for storing images
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

def capture_image(resolution=(640, 480), filename=None):
    """
    Capture an image using the Raspberry Pi camera.
    
    Args:
        resolution: Tuple of (width, height) for image resolution
        filename: Optional filename to save the image
    
    Returns:
        str: Path to the saved image, or None if failed
    """
    # Generate filename if not provided
    if filename is None:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"image_{timestamp}.jpg"
    
    image_path = os.path.join(IMAGE_DIR, filename)
    
    try:
        with PiCamera() as camera:
            # Allow camera to warm up
            camera.resolution = resolution
            camera.start_preview()
            time.sleep(2)  # Camera warm-up time
            
            # Capture the image
            camera.capture(image_path)
            logger.info(f"Image captured: {image_path}")
            
            return image_path
    
    except Exception as e:
        logger.error(f"Error capturing image: {e}")
        return None

def adjust_camera_settings(brightness=50, contrast=50):
    """
    Adjust camera settings.
    
    Args:
        brightness: Brightness level (0-100)
        contrast: Contrast level (0-100)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with PiCamera() as camera:
            camera.brightness = brightness
            camera.contrast = contrast
            logger.info(f"Camera settings adjusted: brightness={brightness}, contrast={contrast}")
            return True
    
    except Exception as e:
        logger.error(f"Error adjusting camera settings: {e}")
        return False

def capture_multiple_images(count=5, delay=1, resolution=(640, 480)):
    """
    Capture multiple images in sequence.
    
    Args:
        count: Number of images to capture
        delay: Delay between captures in seconds
        resolution: Image resolution
    
    Returns:
        list: List of paths to the saved images
    """
    image_paths = []
    
    try:
        with PiCamera() as camera:
            # Set up camera
            camera.resolution = resolution
            camera.start_preview()
            time.sleep(2)  # Camera warm-up
            
            # Capture images
            for i in range(count):
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"image_{timestamp}_{i}.jpg"
                image_path = os.path.join(IMAGE_DIR, filename)
                
                camera.capture(image_path)
                image_paths.append(image_path)
                
                logger.info(f"Captured image {i+1}/{count}: {image_path}")
                
                if i < count - 1:  # No need to wait after the last image
                    time.sleep(delay)
            
            return image_paths
    
    except Exception as e:
        logger.error(f"Error capturing multiple images: {e}")
        return image_paths  # Return any images that were captured before the error