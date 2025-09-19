"""Core unit and pitch system derived from Molly configuration."""

from __future__ import annotations

from dataclasses import dataclass

from brickgpt.printer.units import CanonicalUnits, DEFAULT_UNITS

from .config import MollyConfig


@dataclass(frozen=True, slots=True)
class PitchSystem:
    stud_pitch_mm: float
    layer_height_mm: float
    voxel_size_mm: float
    ldu_per_mm: float = DEFAULT_UNITS.ldu_per_mm

    @property
    def canonical(self) -> CanonicalUnits:
        return CanonicalUnits(
            stud_pitch_mm=self.stud_pitch_mm,
            plate_height_mm=self.layer_height_mm,
            ldu_per_mm=self.ldu_per_mm,
        )

    @property
    def studs_per_voxel(self) -> float:
        return self.voxel_size_mm / self.stud_pitch_mm

    @property
    def plates_per_voxel(self) -> float:
        return self.voxel_size_mm / self.layer_height_mm

    @property
    def brick_height_mm(self) -> float:
        return self.layer_height_mm * 3.0

    def mm_to_studs(self, value_mm: float) -> float:
        return value_mm / self.stud_pitch_mm

    def studs_to_mm(self, studs: float) -> float:
        return studs * self.stud_pitch_mm

    def mm_to_ldu(self, value_mm: float) -> float:
        return value_mm * self.ldu_per_mm

    def ldu_to_mm(self, value_ldu: float) -> float:
        return value_ldu / self.ldu_per_mm

    def quantize_height_mm(self, value_mm: float) -> float:
        bricks = round(value_mm / self.brick_height_mm)
        return bricks * self.brick_height_mm

    def quantize_studs(self, value_mm: float) -> int:
        return int(round(self.mm_to_studs(value_mm)))


def pitch_from_config(config: MollyConfig) -> PitchSystem:
    vox = config.voxelization
    return PitchSystem(
        stud_pitch_mm=vox.pitch_mm,
        layer_height_mm=vox.layer_height_mm,
        voxel_size_mm=vox.voxel_size_mm,
        ldu_per_mm=DEFAULT_UNITS.ldu_per_mm,
    )

