"""
Unit tests for molvis_core.geometry module.

Tests geometric calculations including centroid, rotation matrices,
and coordinate transformations.
"""

import pytest
import numpy as np
from molvis_core import geometry
from molvis_core.exceptions import (
    InvalidCoordinatesError,
    InvalidRotationError,
    DimensionMismatchError,
)


class TestCalculateCentroid:
    """Tests for calculate_centroid function."""

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_centroid_simple(self):
        """Test centroid of simple coordinate set."""
        coords = np.array([
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [1.0, 2.0, 0.0]
        ])

        centroid = geometry.calculate_centroid(coords)
        expected = np.array([1.0, 2.0/3.0, 0.0])

        np.testing.assert_array_almost_equal(centroid, expected)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_centroid_single_point(self):
        """Test centroid of single point."""
        coords = np.array([[1.5, 2.5, 3.5]])

        centroid = geometry.calculate_centroid(coords)

        np.testing.assert_array_equal(centroid, np.array([1.5, 2.5, 3.5]))

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_centroid_empty(self):
        """Test centroid of empty array returns zeros."""
        coords = np.array([]).reshape(0, 3)

        centroid = geometry.calculate_centroid(coords)

        np.testing.assert_array_equal(centroid, np.zeros(3))

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_centroid_symmetric(self):
        """Test centroid of symmetric points around origin."""
        coords = np.array([
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0]
        ])

        centroid = geometry.calculate_centroid(coords)

        np.testing.assert_array_almost_equal(centroid, np.zeros(3))

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_centroid_invalid_shape(self):
        """Test that invalid shape raises error."""
        coords = np.array([1.0, 2.0, 3.0])  # 1D array

        with pytest.raises(InvalidCoordinatesError, match="shape \\(N, 3\\)"):
            geometry.calculate_centroid(coords)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_centroid_none(self):
        """Test that None input returns zeros."""
        centroid = geometry.calculate_centroid(None)
        np.testing.assert_array_equal(centroid, np.zeros(3))


class TestBuildRotationMatrix:
    """Tests for build_rotation_matrix function."""

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_identity_rotation(self):
        """Test that zero rotation gives identity matrix."""
        R = geometry.build_rotation_matrix(0.0, 0.0, 0.0)

        np.testing.assert_array_almost_equal(R, np.identity(3))

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_rotation_x_90(self):
        """Test 90 degree rotation around X-axis."""
        R = geometry.build_rotation_matrix(90.0, 0.0, 0.0)

        # Expected rotation matrix for 90 degrees around X
        expected = np.array([
            [1, 0, 0],
            [0, 0, -1],
            [0, 1, 0]
        ])

        np.testing.assert_array_almost_equal(R, expected)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_rotation_y_90(self):
        """Test 90 degree rotation around Y-axis."""
        R = geometry.build_rotation_matrix(0.0, 90.0, 0.0)

        expected = np.array([
            [0, 0, 1],
            [0, 1, 0],
            [-1, 0, 0]
        ])

        np.testing.assert_array_almost_equal(R, expected)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_rotation_z_90(self):
        """Test 90 degree rotation around Z-axis."""
        R = geometry.build_rotation_matrix(0.0, 0.0, 90.0)

        expected = np.array([
            [0, -1, 0],
            [1, 0, 0],
            [0, 0, 1]
        ])

        np.testing.assert_array_almost_equal(R, expected)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_rotation_matrix_orthogonal(self):
        """Test that rotation matrices are orthogonal."""
        angles = [(45, 30, 60), (90, 45, 180), (123, 234, 345)]

        for angle_x, angle_y, angle_z in angles:
            R = geometry.build_rotation_matrix(angle_x, angle_y, angle_z)

            # R @ R.T should be identity
            np.testing.assert_array_almost_equal(
                R @ R.T,
                np.identity(3)
            )

            # Determinant should be 1
            assert np.abs(np.linalg.det(R) - 1.0) < 1e-10

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_rotation_180(self):
        """Test 180 degree rotation."""
        R = geometry.build_rotation_matrix(180.0, 0.0, 0.0)

        # Rotating 180 degrees around X should flip Y and Z
        expected = np.array([
            [1, 0, 0],
            [0, -1, 0],
            [0, 0, -1]
        ])

        np.testing.assert_array_almost_equal(R, expected, decimal=10)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_rotation_negative_angles(self):
        """Test negative angle rotations."""
        R_pos = geometry.build_rotation_matrix(90.0, 0.0, 0.0)
        R_neg = geometry.build_rotation_matrix(-90.0, 0.0, 0.0)

        # R_neg should be inverse (transpose) of R_pos
        np.testing.assert_array_almost_equal(R_neg, R_pos.T)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_rotation_360(self):
        """Test 360 degree rotation equals identity."""
        R = geometry.build_rotation_matrix(360.0, 360.0, 360.0)

        np.testing.assert_array_almost_equal(R, np.identity(3))


class TestApplyTransform:
    """Tests for apply_transform function."""

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_apply_identity_transform(self):
        """Test applying identity transformation."""
        coords = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0]
        ])

        result = geometry.apply_transform(
            coords,
            rotation_matrix=np.identity(3),
            translation_vector=np.zeros(3)
        )

        np.testing.assert_array_almost_equal(result, coords)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_apply_translation_only(self):
        """Test applying translation only."""
        coords = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0]
        ])
        translation = np.array([5.0, 10.0, 15.0])

        result = geometry.apply_transform(
            coords,
            rotation_matrix=np.identity(3),
            translation_vector=translation
        )

        expected = coords + translation
        np.testing.assert_array_almost_equal(result, expected)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_apply_rotation_around_centroid(self):
        """Test rotation around centroid."""
        # Square in XY plane
        coords = np.array([
            [1.0, 1.0, 0.0],
            [-1.0, 1.0, 0.0],
            [-1.0, -1.0, 0.0],
            [1.0, -1.0, 0.0]
        ])

        # 90 degree rotation around Z
        rotation = geometry.build_rotation_matrix(0.0, 0.0, 90.0)

        result = geometry.apply_transform(
            coords,
            rotation_matrix=rotation,
            translation_vector=np.zeros(3)
        )

        # After 90 degree rotation, points should be rotated
        # Centroid should remain at origin
        result_centroid = np.mean(result, axis=0)
        np.testing.assert_array_almost_equal(result_centroid, np.zeros(3))

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_apply_rotation_around_custom_center(self):
        """Test rotation around custom center."""
        coords = np.array([[1.0, 0.0, 0.0]])
        rotation = geometry.build_rotation_matrix(0.0, 0.0, 90.0)
        center = np.array([0.0, 0.0, 0.0])

        result = geometry.apply_transform(
            coords,
            rotation_matrix=rotation,
            translation_vector=np.zeros(3),
            center_of_rotation=center
        )

        # Point at (1, 0, 0) rotated 90 degrees around origin should be at (0, 1, 0)
        expected = np.array([[0.0, 1.0, 0.0]])
        np.testing.assert_array_almost_equal(result, expected, decimal=10)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_apply_combined_transform(self):
        """Test applying rotation and translation together."""
        coords = np.array([[1.0, 0.0, 0.0]])
        rotation = geometry.build_rotation_matrix(0.0, 0.0, 90.0)
        translation = np.array([10.0, 20.0, 30.0])

        # Test with explicit center_of_rotation at origin
        result = geometry.apply_transform(
            coords,
            rotation_matrix=rotation,
            translation_vector=translation,
            center_of_rotation=np.array([0.0, 0.0, 0.0])
        )

        # Point at (1, 0, 0) rotated 90 degrees around origin becomes (0, 1, 0)
        # Then translated by (10, 20, 30) to get (10, 21, 30)
        expected = np.array([[10.0, 21.0, 30.0]])
        np.testing.assert_array_almost_equal(result, expected, decimal=10)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_apply_transform_empty(self):
        """Test transform on empty coordinates."""
        coords = np.array([]).reshape(0, 3)

        result = geometry.apply_transform(
            coords,
            rotation_matrix=np.identity(3),
            translation_vector=np.zeros(3)
        )

        assert result.size == 0

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_apply_transform_invalid_shapes(self):
        """Test that invalid input shapes raise errors."""
        coords = np.array([[1.0, 2.0, 3.0]])

        # Invalid rotation matrix shape
        with pytest.raises(DimensionMismatchError):
            geometry.apply_transform(
                coords,
                rotation_matrix=np.identity(2),
                translation_vector=np.zeros(3)
            )

        # Invalid translation vector shape
        with pytest.raises(DimensionMismatchError):
            geometry.apply_transform(
                coords,
                rotation_matrix=np.identity(3),
                translation_vector=np.zeros(2)
            )

        # Invalid coords shape
        with pytest.raises(InvalidCoordinatesError):
            geometry.apply_transform(
                np.array([1.0, 2.0, 3.0]),
                rotation_matrix=np.identity(3),
                translation_vector=np.zeros(3)
            )


class TestGeometryEdgeCases:
    """Tests for edge cases in geometry functions."""

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_very_large_coords(self):
        """Test handling of very large coordinates."""
        coords = np.array([[1e10, 1e10, 1e10]])
        centroid = geometry.calculate_centroid(coords)

        np.testing.assert_array_almost_equal(centroid, coords[0])

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_very_small_coords(self):
        """Test handling of very small coordinates."""
        coords = np.array([[1e-10, 1e-10, 1e-10]])
        centroid = geometry.calculate_centroid(coords)

        np.testing.assert_array_almost_equal(centroid, coords[0])

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_rotation_commutativity(self):
        """Test that rotation order matters (not commutative)."""
        R1 = geometry.build_rotation_matrix(90.0, 45.0, 0.0)
        R2 = geometry.build_rotation_matrix(45.0, 90.0, 0.0)

        # Should not be equal (rotations don't commute)
        assert not np.allclose(R1, R2)
