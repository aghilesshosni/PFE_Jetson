import sys
import os
import time
import logging

current_dir=os.path.dirname(os.path.abspath(__file__))
parent_dir=os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from vision.vision_main import VisionMain

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHnadler(sys.stdout), logging.FileHandler('/PFE_Jetson/logs/PFE_Jetson.log')])
logger = logging.getLogger("PFE_Jetson_Main")

class ApplicationMaster:
    def __init__(self):
        logger.info("Inititalisation ....")
        try:
            self.vision_system= VisionMain()
            logger.info("Sous Systemes de vision charges avec Succes")
        except Exception as e:
            logger.error("Echec critique lors de chargement des modules : {}'.format(e))
            raise

    def run(self):
        logger.info("Demarrage de la Boucle Principale...")
        try:
            if not self.vision_system.start():
                logger.error("Impossible de demarrer le systeme de vision")
                return
            while True:
                self.vision_system.run()
        except KeyboardInterrupt:
            logger.info("Interruption Manuelle")
        except Exception as e:
            logger.error("Erreur critique dans la boucle principale : {}".format(e))
        finally:
            self.stop()

    def stop(self):
        logger.info("Arret de systeme de vision")
        self.vision_systeme.arreter()

        logger.info("Systeme arrete")

if __name__=="__main__":
    app=ApplicationMaster()
    app.run()
