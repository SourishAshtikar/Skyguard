"""
SkyGuard AI — Alert Deduplication & Notification Throttler
Prevents notification spam during active incidents while ensuring critical escalations
and state transitions immediately bypass cooldown.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from skyguard.config.settings import SETTINGS


class AlertDeduplicator:
    """Manages alert throttling, deduplication, and notification rules."""

    def __init__(self):
        # Maps incident_id -> Dict of last notification details
        self.last_notifications: Dict[str, Dict[str, Any]] = {}

    def should_emit_notification(self, incident: Dict[str, Any], is_critical_escalation: bool = False) -> Tuple[bool, str]:
        """
        Determines whether a notification should be dispatched for an incident.
        
        Returns:
            Tuple (should_emit: bool, reason: str)
        """
        inc_id = incident["incident_id"]
        status = incident["status"]
        severity = incident["severity"]

        now = datetime.now(timezone.utc)

        # 1. Critical escalations ALWAYS bypass cooldown
        if is_critical_escalation or severity == "CRITICAL":
            self.last_notifications[inc_id] = {"timestamp": now, "severity": severity, "status": status}
            return True, "CRITICAL_ESCALATION_BYPASS"

        if inc_id not in self.last_notifications:
            # First notification for incident
            self.last_notifications[inc_id] = {"timestamp": now, "severity": severity, "status": status}
            return True, "INITIAL_ALERT"

        last_notif = self.last_notifications[inc_id]
        last_time = last_notif["timestamp"]
        last_severity = last_notif["severity"]
        last_status = last_notif["status"]

        # 2. State changes (e.g. RECOVERING, RESOLVED) trigger notifications immediately
        if status != last_status:
            self.last_notifications[inc_id] = {"timestamp": now, "severity": severity, "status": status}
            return True, f"STATUS_CHANGE_{status}"

        # 3. Severity escalation triggers notification
        if severity != last_severity:
            self.last_notifications[inc_id] = {"timestamp": now, "severity": severity, "status": status}
            return True, f"SEVERITY_CHANGE_{severity}"

        # 4. Check cooldown window for continued active incident
        elapsed = (now - last_time).total_seconds()
        if elapsed >= SETTINGS.alert_cooldown_seconds:
            self.last_notifications[inc_id] = {"timestamp": now, "severity": severity, "status": status}
            return True, "COOLDOWN_EXPIRED"

        # Suppressed due to cooldown
        return False, f"SUPPRESSED_COOLDOWN_{int(SETTINGS.alert_cooldown_seconds - elapsed)}s_REMAINING"


# Global Deduplicator Instance
DEDUPLICATOR = AlertDeduplicator()
