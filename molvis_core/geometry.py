"""
molvis_core/geometry.py

Provides functions for geometric calculations and transformations relevant
to molecular visualization.
"""

import numpy as np
from typing import Optional


def calculate_centroid(coords: np.ndarray) -> np.ndarray:
    """
    Calculates the geometric centroid (mean position) of a set of coordinates.

    Args:
        coords: A NumPy array of shape (N, 3) representing atomic coordinates.

    Returns:
        A NumPy array (3,) representing the (x, y, z) centroid,
        or [0, 0, 0] if the input array is empty or invalid.
    """
    if coords is None or coords.size == 0:
        return np.zeros(3)
    if coords.ndim != 2 or coords.shape[1] != 3:
        raise ValueError("Input coords must be a NumPy array of shape (N, 3)")
    return np.mean(coords, axis=0)


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
    """
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
    return R_z @ R_y @ R_x


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
        ValueError: If input shapes are incorrect.
    """
    if coords.size == 0:
        return np.array([])  # Return empty if input is empty
    if coords.ndim != 2 or coords.shape[1] != 3:
        raise ValueError("Input coords must be a NumPy array of shape (N, 3)")
    if rotation_matrix.shape != (3, 3):
        raise ValueError("rotation_matrix must be a 3x3 NumPy array")
    if translation_vector.shape != (3,):
        raise ValueError("translation_vector must be a NumPy array of shape (3,)")

    # Determine the center of rotation
    if center_of_rotation is None:
        center = calculate_centroid(coords)
    else:
        if center_of_rotation.shape != (3,):
            raise ValueError("center_of_rotation must be a NumPy array of shape (3,)")
        center = center_of_rotation

    # Translate coordinates so the center of rotation is at the origin
    coords_centered = coords - center
    # Apply rotation (Note: vectors @ R.T for row vectors)
    coords_rotated = coords_centered @ rotation_matrix.T
    # Translate back from the origin
    coords_recentered = coords_rotated + center
    # Apply final translation
    transformed_coords = coords_recentered + translation_vector

    return transformed_coords
