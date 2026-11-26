from nautobot.apps.jobs import register_jobs

from .fabric_report import FabricReport

register_jobs(FabricReport)
