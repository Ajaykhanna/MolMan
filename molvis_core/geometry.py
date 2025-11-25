"""
molvis_core/geometry.py

Provides functions for geometric calculations and transformations relevant
to molecular visualization.
"""

import numpy as np
from typing import Optional

from .logging_config import get_logger
from .exceptions import (
    InvalidCoordinatesError,
    InvalidRotationError,
    InvalidTransformationError,
    DimensionMismatchError,
)

# Initialize logger for this module
logger = get_logger(__name__)


def calculate_centroid(coords: np.ndarray) -> np.ndarray:
    """
    Calculates the geometric centroid (mean position) of a set of coordinates.

    Args:
        coords: A NumPy array of shape (N, 3) representing atomic coordinates.

    Returns:
        A NumPy array (3,) representing the (x, y, z) centroid,
        or [0, 0, 0] if the input array is empty or invalid.

    Raises:
        InvalidCoordinatesError: If coordinates have invalid shape
    """
    logger.debug(f"Calculating centroid for {coords.shape if coords is not None else 'None'}")

    if coords is None or coords.size == 0:
        logger.warning("Empty or None coordinates provided, returning zero centroid")
        return np.zeros(3)

    if coords.ndim != 2 or coords.shape[1] != 3:
        logger.error(f"Invalid coordinate shape: {coords.shape}, expected (N, 3)")
        raise InvalidCoordinatesError(
            f"Input coords must be a NumPy array of shape (N, 3), got {coords.shape}"
        )

    centroid = np.mean(coords, axis=0)
    logger.debug(f"Calculated centroid: {centroid}")
    return centroid


def build_rotation_matrix(
    angle_x_deg: float, angle_y_deg: float, angle_z_deg: float
) -> np.ndarray:
    """
    Builds a combined 3D rotation matrix using ZYX Tait-Bryan convention.

    Rotation is applied in the order: X, then Y, then Z.

    Args:
        angle_x_deg: Rotation angle around X-axis in degrees.
        angle_y_deg: Rotation angle around Y-axis in degrees.
        angle_z_deg: Rotation angle around Z-axis in degrees.

    Returns:
        A 3x3 NumPy rotation matrix (R = Rz * Ry * Rx).

    Raises:
        InvalidRotationError: If angles are invalid (NaN or infinite)
    """
    logger.debug(
        f"Building rotation matrix: X={angle_x_deg}°, Y={angle_y_deg}°, Z={angle_z_deg}°"
    )

    # Validate angles
    if not all(np.isfinite([angle_x_deg, angle_y_deg, angle_z_deg])):
        logger.error("Invalid rotation angles: values must be finite")
        raise InvalidRotationError("Rotation angles must be finite values")

    theta_x, theta_y, theta_z = (
        np.radians(angle_x_deg),
        np.radians(angle_y_deg),
        np.radians(angle_z_deg),
    )
    cos_x, sin_x = np.cos(theta_x), np.sin(theta_x)
    cos_y, sin_y = np.cos(theta_y), np.sin(theta_y)
    cos_z, sin_z = np.cos(theta_z), np.sin(theta_z)

    # Rotation matrix around X
    R_x = np.array([[1, 0, 0], [0, cos_x, -sin_x], [0, sin_x, cos_x]])
    # Rotation matrix around Y
    R_y = np.array([[cos_y, 0, sin_y], [0, 1, 0], [-sin_y, 0, cos_y]])
    # Rotation matrix around Z
    R_z = np.array([[cos_z, -sin_z, 0], [sin_z, cos_z, 0], [0, 0, 1]])

    # Combined rotation: Apply R_x, then R_y, then R_z
    # Matrix multiplication order is R_z @ R_y @ R_x
    # To apply to row vectors (N x 3 array): result = vectors @ R.T
    rotation_matrix = R_z @ R_y @ R_x
    logger.debug("Successfully built rotation matrix")
    return rotation_matrix


def apply_transform(
    coords: np.ndarray,
    rotation_matrix: np.ndarray,
    translation_vector: np.ndarray,
    center_of_rotation: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Applies rotation and translation to a set of coordinates.

    Rotation is performed around the specified center_of_rotation (or the
    centroid of the coordinates if None is provided).

    Args:
        coords: NumPy array (N, 3) of coordinates to transform.
        rotation_matrix: 3x3 NumPy array for rotation.
        translation_vector: NumPy array (3,) for translation.
        center_of_rotation: NumPy array (3,) specifying the point to rotate
                            around. If None, the centroid of `coords` is used.

    Returns:
        A new NumPy array (N, 3) containing the transformed coordinates.

    Raises:
        InvalidCoordinatesError: If coordinates have invalid shape
        InvalidTransformationError: If transformation parameters are invalid
        DimensionMismatchError: If array dimensions don't match
    """
    logger.debug(
        f"Applying transform to {coords.shape[0] if coords.size > 0 else 0} atoms"
    )

    if coords.size == 0:
        logger.warning("Empty coordinates provided, returning empty array")
        return np.array([])  # Return empty if input is empty

    if coords.ndim != 2 or coords.shape[1] != 3:
        logger.error(f"Invalid coordinate shape: {coords.shape}")
        raise InvalidCoordinatesError(
            f"Input coords must be a NumPy array of shape (N, 3), got {coords.shape}"
        )

    if rotation_matrix.shape != (3, 3):
        logger.error(f"Invalid rotation matrix shape: {rotation_matrix.shape}")
        raise DimensionMismatchError("(3, 3)", str(rotation_matrix.shape))

    if translation_vector.shape != (3,):
        logger.error(f"Invalid translation vector shape: {translation_vector.shape}")
        raise DimensionMismatchError("(3,)", str(translation_vector.shape))

    # Determine the center of rotation
    if center_of_rotation is None:
        center = calculate_centroid(coords)
        logger.debug(f"Using calculated centroid as rotation center: {center}")
    else:
        if center_of_rotation.shape != (3,):
            logger.error(f"Invalid center_of_rotation shape: {center_of_rotation.shape}")
            raise DimensionMismatchError("(3,)", str(center_of_rotation.shape))
        center = center_of_rotation
        logger.debug(f"Using provided rotation center: {center}")

    # Translate coordinates so the center of rotation is at the origin
    coords_centered = coords - center
    # Apply rotation (Note: vectors @ R.T for row vectors)
    coords_rotated = coords_centered @ rotation_matrix.T
    # Translate back from the origin
    coords_recentered = coords_rotated + center
    # Apply final translation
    transformed_coords = coords_recentered + translation_vector

    logger.debug(f"Successfully transformed {coords.shape[0]} atoms")
    return transformed_coords
