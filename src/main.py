# -*- coding: utf-8 -*-
import sys
import os
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from web_dashboard.app import start_dashboard_thread
from vision.vision_main import VisionMain

log_dir  = os.path.join(parent_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(log_dir, "PFE_Jetson.log"))
    ]
)
logger = logging.getLogger("PFE_Jetson_Main")


class ApplicationMaster:
    def __init__(self):
        logger.info("Initialisation...")
        try:
            self.vision_system = VisionMain()
            logger.info("Systeme de vision charge avec succes")
        except Exception as e:
            logger.error("Echec critique: {}".format(e))
            raise

    def run(self):
        logger.info("Demarrage...")
        start_dashboard_thread()
        try:
            if not self.vision_system.start():
                logger.error("Impossible de demarrer le systeme de vision")
                return
            self.vision_system.run()
        except KeyboardInterrupt:
            logger.info("Interruption manuelle")
        except Exception as e:
            logger.error("Erreur critique: {}".format(e))
        finally:
            self.stop()

    def stop(self):
        logger.info("Arret du systeme...")
        self.vision_system.arreter()
        logger.info("Systeme arrete")


if __name__ == "__main__":
    ApplicationMaster().run()
