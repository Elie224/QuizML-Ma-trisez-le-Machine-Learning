# QCM ML Mobile

Application mobile React Native (Expo) connectée à l'API QCM existante.

## Prérequis

- Node.js 20+
- npm
- Expo Go sur smartphone ou émulateur Android/iOS
- API QCM en cours d'exécution

## Installation

```bash
cd mobile
npm install
```

## Lancement

```bash
npm run start
```

Puis:
- `a` pour Android emulator
- `i` pour iOS simulator (macOS)
- scanner le QR code avec Expo Go

## Configuration API

Dans l'écran "Serveur API", renseigne l'URL de ton backend.

Valeurs utiles:
- Android emulator: `http://10.0.2.2:8011`
- iOS simulator: `http://127.0.0.1:8011`
- Smartphone physique (même Wi-Fi): `http://IP_DE_TON_PC:8011`

L'URL est sauvegardée localement sur le mobile.

## Fonctions incluses

- Démarrage de session QCM (thème, catégorie, 10 questions fixes)
- Réponse question par question avec feedback
- Affichage score et progression
- Consultation du top leaderboard


## Structure de session

- 5 catégories: facile, moyen, difficile, très difficile, expert
- 10 questions fixes pour la catégorie choisie