import json
import logging
import os
import sys
import time

import requests

BASE_DIR= os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE= os.path.join(BASE_DIR, "config.json")
DEFAULT_CONFIG = {
    "api_url": "https://fans.ouepamal.fr/ilo-fans-controller/index.php?api=fans",   # L'url de l'API de ton ilo fans controller WALAHHHH
    "interval": 60, #  Temps entre chaque requête en sec :]
    "fan_limit": 40, # x% max de vitesse des ventilos avant que ça set à fan_set
    "fan_set": 15, # x% de vitesse des ventilos à mettre si on dépasse fan_limit
    "request_timeout": 20, # Temps avant que ta requete elle échoue et qu'elle retourne au Daghestan
}

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def create_default_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
    print(f"Le fichiere de config à été créer: {CONFIG_FILE}")
    print("Pense à le config parce que sinon ça va pas trop marcher :]")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        create_default_config()
        sys.exit(0)

    try:
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
    except Exception as e:
        logging.error(f"Petit soucis dans ta config: {e}")
        sys.exit(0)

    required_keys = ["api_url", "interval", "fan_limit", "fan_set", "request_timeout"]
    for key in required_keys:
        if key not in config:
            logging.error(f"Ta config est pas complète, il manque: {key}")
            sys.exit(0)

    config.setdefault("request_timeout", 20)

    if not isinstance(config["interval"], int) or config["interval"] <= 0:
        logging.error("L'interval doit être un entier positif.")
        sys.exit(0)

    if not isinstance(config["fan_limit"], int) or not (0 <= config["fan_limit"] <= 100):
        logging.error("Le fan_limit doit être un entier entre 0 et 100 sinon bah ça fait pfiouuuu.")
        sys.exit(0)

    if not isinstance(config["fan_set"], int) or not (0 <= config["fan_set"] <= 100):
        logging.error("Le fan_set doit être un entier entre 0 et 100 sinon bah il se met à voler.")
        sys.exit(0)

    if config["fan_set"] > config["fan_limit"]:
        logging.warning("Le fan_set ({}) doit être inférieur ou égal au fan_limit ({}) sinon ça va pas trop marcher.".format(config["fan_set"], config["fan_limit"]))
        sys.exit(0)

    return config


def get_fans(config):
    try:
        response = requests.get(config["api_url"], timeout=config["request_timeout"], params={"api": "fans"})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Erreur lors de la récupération des vitesses des ventilos: {e}")
        return None
    except ValueError as e:
        logging.error(f"La réponse JSON je la comprennd pas trop: {e}")
        return None


def set_fans(config, fan_values):
    url = config["api_url"]
    timeout = config["request_timeout"]

    payload = {"action": "fans", "fans": fan_values}

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        logging.info(f"Vitesse mise à jour pour les ventilos actifs: {fan_values}")
        return True
    except requests.RequestException as e:
        logging.error(f"Erreur lors de la mise à jour des vitesses des ventilos: {e}")
        return False


def check_fans(config):
    fans = get_fans(config)

    if fans is None:
        logging.error("Impossible de récupérer les vitesses des ventilos.")
        return

    limit = config["fan_limit"]
    set_speed = config["fan_set"]

    active_fans = {}
    exceeded = False

    for fan_name, speed in fans.items():
        try:
            speed = int(speed)
        except (ValueError, TypeError):
            logging.error(f"Vitesse du ventilo {fan_name} invalide: {speed}")
            continue

        logging.info(f"Vitesse du ventilo {fan_name}: {speed}%")

        if speed <= 0:
            logging.info(f"Ventilo {fan_name} absent, ignoré.")
            continue

        active_fans[fan_name] = set_speed

        if speed > limit:
            exceeded = True
            logging.warning(f"Vitesse du ventilo {fan_name} ({speed}%) dépasse la limite ({limit}%).")

    if not active_fans:
        logging.info("Aucun ventilo présent détecté.")
        return

    if exceeded:
        logging.warning(f"Au moins un ventilo dépasse la limite de {limit}%.")
        for fan_name, target_speed in active_fans.items():
            logging.info(f"Set ventilo '{fan_name}' à {target_speed}%")
        set_fans(config, active_fans)
    else:
        logging.info("Tous les ventilos sont dans la limite YOUPIII.")


def main():
    setup_logging()
    config = load_config()

    logging.info("=== TAISEZ VOUS VENTILOS - by OuePaMal ===")
    logging.info(f"Intervalle de vérification: {config['interval']} secondes")
    logging.info(f"Limite de vitesse des ventilos: {config['fan_limit']}%")
    logging.info(f"Vitesse des ventilos à mettre si ça vole à besogne: {config['fan_set']}%")

    while True:
        try:
            check_fans(config)
        except Exception as e:
            logging.error(f"Une erreur est survenue ohlala...: {e}")
        time.sleep(config["interval"])


if __name__ == "__main__":
    main()


    