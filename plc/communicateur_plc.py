# -*- coding: utf-8 -*-
import asyncio
import logging
from asyncua import Client
# Ajout des imports requis pour le formatage des données Siemens
from asyncua.ua import DataValue, Variant, VariantType

logger = logging.getLogger("CommunicateurPLC")

class CommunicateurPLC:
    def __init__(self, ip, port=4840):
        self.url = "opc.tcp://{}:{}".format(ip, port)
        self.client = Client(url=self.url)
        self.connecte = False

        self.NODE_BOUTEILLE = 'ns=4;i=3'
        self.NODE_NIVEAU    = 'ns=4;i=4'
    async def connecter(self):
        try:
            await self.client.connect()
            self.connecte = True
            logger.info("Connecte au PLC: {}".format(self.url))
        except Exception as e:
            self.connecte = False
            logger.error("Echec connexion PLC: {}".format(e))

    async def envoyer(self, bouteille_presente, niveau_pct):
        if not self.connecte:
            return
        try:
            node_b = self.client.get_node(self.NODE_BOUTEILLE)
            node_n = self.client.get_node(self.NODE_NIVEAU)

            await node_b.write_value(DataValue(Variant(bool(bouteille_presente), VariantType.Boolean)))
            await node_n.write_value(DataValue(Variant(float(niveau_pct), VariantType.Float)))

            logger.info("Envoye -> bouteille: {} | niveau: {:.1f}%".format(
                bouteille_presente, niveau_pct))
        except Exception as e:
            logger.error("Erreur envoi PLC: {}".format(e))
            self.connecte = False

    async def deconnecter(self):
        if self.connecte:
            await self.client.disconnect()
            logger.info("Deconnecte du PLC")


async def test_standalone():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    plc = CommunicateurPLC(ip="192.168.0.20", port=4840)
    await plc.connecter()

    if not plc.connecte:
        print("Impossible de se connecter au PLC.")
        return

    print("Connexion OK — envoi de TRUE en continu...")
    try:
        while True:
            await plc.envoyer(True, 50.0)
            print("Envoye -> bouteille=True | niveau=50.0%")
            await asyncio.sleep(0.5)
    except KeyboardInterrupt:
        print("\nArret")
    finally:
        await plc.deconnecter()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_standalone())
    loop.close()
