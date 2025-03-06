import sys
import logging

from reporting.connection import MotherDuckConnection
from reporting.query_registry import QueryRegistry
from reporting.runner import ReportingRunner

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s %(name)s: %(levelname)-4s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


runner = ReportingRunner(
    query_registry=QueryRegistry(), connection=MotherDuckConnection()
)
runner.run()
