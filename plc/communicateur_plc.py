# -*- coding: utf-8 -*-
import asyncio
import logging
from asyncua import Client
from asyncua.ua import DataValue, Variant, VariantType

logger = logging.getLogger("CommunicateurPLC")


class CommunicateurPLC:
    def __init__(self, ip, port=4840):
        self.url     = "opc.tcp://{}:{}".format(ip, port)
        self.client  = Client(url=self.url)
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
            await node_b.write_value(
                DataValue(Variant(bool(bouteille_presente),
                                  VariantType.Boolean)))
            await node_n.write_value(
                DataValue(Variant(float(niveau_pct),
                                  VariantType.Float)))
            logger.info("Envoye -> bouteille:{} | niveau:{:.1f}%".format(
                bouteille_presente, niveau_pct))
        except Exception as e:
            logger.error("Erreur envoi PLC: {}".format(e))
            self.connecte = False

    async def lire_valeurs(self):
        if not self.connecte:
            return None, None
        try:
            node_b    = self.client.get_node(self.NODE_BOUTEILLE)
            node_n    = self.client.get_node(self.NODE_NIVEAU)
            bouteille = await node_b.read_value()
            niveau    = await node_n.read_value()
            return bouteille, niveau
        except Exception as e:
            logger.error("Erreur lecture PLC: {}".format(e))
            return None, None

    async def deconnecter(self):
        if self.connecte:
            await self.client.disconnect()
            self.connecte = False
            logger.info("Deconnecte du PLC")


async def test_standalone():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    plc = CommunicateurPLC(ip="192.168.0.20", port=4840)
    await plc.connecter()

    if not plc.connecte:
        print("Impossible de se connecter.")
        print("Verifiez :")
        print("  — Automate allume et en RUN")
        print("  — IP correcte : 192.168.0.20")
        print("  — OPC UA active dans TIA Portal")
        return

    print("=" * 50)
    print("Connexion OK — automate reel S7-1200")
    print("Nodes : ns=4;i=3 | ns=4;i=4")
    print("Ctrl+C pour arreter")
    print("=" * 50)

    niveau    = 0.0
    bouteille = True

    try:
        while True:
            if bouteille:
                niveau = min(niveau + 1.5, 100.0)
                if niveau >= 100.0:
                    print("\nBouteille pleine — retrait simulation")
                    bouteille = False
                    niveau    = 0.0
            else:
                await asyncio.sleep(3)
                bouteille = True
                print("Nouvelle bouteille")

            await plc.envoyer(bouteille, niveau)

            b, n = await plc.lire_valeurs()
            print("ENVOYE  -> bouteille={} | niveau={:.1f}%".format(
                bouteille, niveau))
            if b is not None:
                print("RECU PLC-> bouteille={} | niveau={:.1f}%".format(
                    b, n))
            print("-" * 40)

            await asyncio.sleep(0.5)

    except KeyboardInterrupt:
        print("\nArret")
    finally:
        await plc.deconnecter()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_standalone())
    loop.close()
