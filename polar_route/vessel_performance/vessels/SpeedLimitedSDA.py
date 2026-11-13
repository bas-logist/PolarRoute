import numpy as np
from polar_route.vessel_performance.vessels.SDA import SDA


class SpeedLimitedSDA(SDA):
    """
    A variation of the SDA model that can apply speed limits built into the environmental mesh.
    See `docs/examples.md` for an example of how to use this class.
    """
    
    def __init__(self, vessel_config):
        super().__init__(vessel_config)
        self.speed_limit_fields = vessel_config.get("speed_limit_fields", [])

    def model_speed(self, cellbox):
        cellbox = super().model_speed(cellbox)
        self.apply_speed_limits(cellbox)
        return cellbox

    def apply_speed_limits(self, cellbox):
        speed = cellbox.agg_data.get("speed", None)
        if speed is None:
            return

        try:
            speed = np.asarray(speed, dtype=float)
        except (TypeError, ValueError):
            return

        limits = []
        for field in self.speed_limit_fields:
            value = cellbox.agg_data.get(field)
            if value is None:
                continue
            try:
                f = float(value)
            except (TypeError, ValueError):
                continue
            if np.isfinite(f):
                limits.append(f)

        if limits:
            speed = np.minimum(speed, min(limits))
            cellbox.agg_data["speed"] = speed.tolist()