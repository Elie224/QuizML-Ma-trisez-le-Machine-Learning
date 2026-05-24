# QCM Machine Learning

Application de QCM orientée apprentissage machine learning.

Fonctionnalités principales:
- Sessions QCM par thème et catégorie
- Correction immédiate avec explication
- Score final et progression par thème
- Leaderboard persistant des meilleurs scores

Structure des catégories:
- facile
- moyen
- difficile
- très difficile
- expert
- 10 questions par session pour la catégorie choisie

Points d'entrée:
- API FastAPI: qcm_api_fr.py
- Interface web native: route GET /

Routes API principales:
- GET /health
- GET /qcm/topics
- GET /qcm/categories
- POST /qcm/sessions
- GET /qcm/sessions/{session_id}
- POST /qcm/sessions/{session_id}/answer
- POST /qcm/leaderboard/submit
- GET /qcm/leaderboard
- GET /qcm/leaderboard.csv

Lancement local:
- API + frontend web: uvicorn qcm_api_fr:app --host 127.0.0.1 --port 8011
- Frontend: http://127.0.0.1:8011/

Application mobile:
- Projet Expo React Native: mobile/
- Installation: cd mobile && npm install
- Démarrage: cd mobile && npx expo start
- Android emulator: configurer l'API sur http://10.0.2.2:8011
- iOS simulator: configurer l'API sur http://127.0.0.1:8011
- L'app mobile suit la même structure à 5 catégories et 10 questions fixes
