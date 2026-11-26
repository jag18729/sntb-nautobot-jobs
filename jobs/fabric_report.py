"""Nautobot Job: read the synthetic fabric from the database and fail on anything wrong.

Thin wrapper. The rules live in fabric_logic.py so they can be tested without Nautobot.
Read-only: it never writes to the database.
"""

from nautobot.apps.jobs import Job, StringVar

from .fabric_logic import check_fabric


class FabricReport(Job):
    """Report the devices tagged as synthetic and fail on any rule violation."""

    tag = StringVar(
        description="Tag that marks the synthetic objects",
        default="sntb-lab-synthetic",
        label="Tag",
    )

    class Meta:
        name = "Synthetic fabric report"
        description = "Read-only. Lists devices with the given tag and fails on rule violations."
        read_only = True
        has_sensitive_variables = False

    def run(self, tag):  # noqa: D102  (Nautobot passes the job variables as keyword arguments)
        from nautobot.dcim.models import Device  # imported late: needs Django ready

        devices = []
        qs = Device.objects.filter(tags__name=tag).select_related("role", "location", "primary_ip4")
        for d in qs:
            devices.append(
                {
                    "name": d.name,
                    "role": d.role.name if d.role else None,
                    "location": d.location.name if d.location else None,
                    "primary_ip": str(d.primary_ip4.host) if d.primary_ip4 else None,
                    "interfaces": d.interfaces.count(),
                }
            )
        report, problems = check_fabric(devices)
        for line in report:
            self.logger.info(line)
        for p in problems:
            self.logger.error(p)
        if problems:
            raise RuntimeError(f"{len(problems)} problem(s) in the synthetic fabric")
        return f"{len(devices)} devices ok"
