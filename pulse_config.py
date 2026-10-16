"""
PulseWorkshop 24x7 - Dynamic Configuration Engine
No hardcoded values: dynamically configurable per dealership site, service line, and SLA policy.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import json
import os

class OperatingHours(BaseModel):
    open_time: str = "09:00"   # HH:MM local
    close_time: str = "18:00"  # HH:MM local
    is_closed: bool = False

class SiteConfig(BaseModel):
    site_id: str = "KTD-04"
    site_name: str = "Sparsh Motors, Kothrud"
    timezone: str = "Asia/Kolkata"
    timezone_offset_minutes: int = 330  # +05:30 IST
    enabled_services: List[str] = Field(default_factory=lambda: ["periodic", "diagnostic", "inspection"])
    bodyshop_enabled: bool = False
    schedule: Dict[str, OperatingHours] = Field(default_factory=lambda: {
        "monday": OperatingHours(open_time="09:00", close_time="18:00"),
        "tuesday": OperatingHours(open_time="09:00", close_time="18:00"),
        "wednesday": OperatingHours(open_time="09:00", close_time="18:00"),
        "thursday": OperatingHours(open_time="09:00", close_time="18:00"),
        "friday": OperatingHours(open_time="09:00", close_time="18:00"),
        "saturday": OperatingHours(open_time="09:00", close_time="18:00"),
        "sunday": OperatingHours(is_closed=True)
    })
    max_transfer_wait_sec: int = 45
    unanswered_rings_threshold: int = 4
    auto_remediation_enabled: bool = True

class SystemConfig(BaseModel):
    active_site_id: str = "KTD-04"
    sites: Dict[str, SiteConfig] = Field(default_factory=dict)
    alert_channels: List[str] = Field(default_factory=lambda: ["websocket", "log"])
    strict_invariant_mode: bool = True

def get_default_config() -> SystemConfig:
    ktd = SiteConfig(
        site_id="KTD-04",
        site_name="Sparsh Motors, Kothrud Workshop",
        timezone="Asia/Kolkata",
        timezone_offset_minutes=330,
        enabled_services=["periodic", "diagnostic", "inspection"],
        bodyshop_enabled=False
    )
    # Add a sample US dealership to demonstrate universal adaptability
    austin = SiteConfig(
        site_id="ATX-01",
        site_name="Lone Star Ford, Austin",
        timezone="America/Chicago",
        timezone_offset_minutes=-300,
        enabled_services=["periodic", "diagnostic", "inspection", "bodyshop"],
        bodyshop_enabled=True,
        schedule={
            "monday": OperatingHours(open_time="07:30", close_time="19:00"),
            "tuesday": OperatingHours(open_time="07:30", close_time="19:00"),
            "wednesday": OperatingHours(open_time="07:30", close_time="19:00"),
            "thursday": OperatingHours(open_time="07:30", close_time="19:00"),
            "friday": OperatingHours(open_time="07:30", close_time="19:00"),
            "saturday": OperatingHours(open_time="08:00", close_time="17:00"),
            "sunday": OperatingHours(is_closed=True)
        }
    )
    return SystemConfig(
        active_site_id="KTD-04",
        sites={"KTD-04": ktd, "ATX-01": austin}
    )

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "pulse_config.json")

def load_config() -> SystemConfig:
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return SystemConfig(**data)
        except Exception:
            pass
    cfg = get_default_config()
    save_config(cfg)
    return cfg

def save_config(cfg: SystemConfig):
    with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg.model_dump(), f, indent=2)

if __name__ == "__main__":
    cfg = load_config()
    print(f"Loaded config for active site: {cfg.active_site_id} ({cfg.sites[cfg.active_site_id].site_name})")
