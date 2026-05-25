import random
import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Lock


QUESTION_BANK_PATH = Path("data/qcm/ml_qcm_fr.json")
QUESTIONS_PER_LEVEL = 10
LEVELS_PER_CATEGORY = 10
CATEGORIES = ["facile", "moyen", "difficile", "tres difficile", "expert"]
CATEGORY_CONTEXT = {
    "facile": "initiation",
    "moyen": "application",
    "difficile": "approfondissement",
    "tres difficile": "avance",
    "expert": "expert",
}
LEVEL_FOCUS = [
    "bases essentielles",
    "fondamentaux appliques",
    "premiers raisonnements",
    "raisonnement structure",
    "consolidation methodique",
    "analyse contextualisee",
    "analyse avancee",
    "resolution de cas complexes",
    "maitrise operationnelle",
    "maitrise complete",
]
CATEGORY_PROMPTS = {
    "facile": "Dans une situation d'initiation au ML,",
    "moyen": "Dans un exercice d'application en ML,",
    "difficile": "Dans un cas d'approfondissement en ML,",
    "tres difficile": "Dans un cas avance de ML,",
    "expert": "Dans une analyse experte de ML,",
}
LEVEL_PROMPTS = [
    "pour verifier les bases essentielles,",
    "pour consolider les fondamentaux appliques,",
    "pour reussir un premier raisonnement autonome,",
    "pour structurer une analyse plus rigoureuse,",
    "pour valider une comprehension solide,",
    "pour traiter un contexte plus nuance,",
    "pour analyser un cas avance,",
    "pour resoudre un probleme complexe,",
    "pour demontrer une maitrise operationnelle,",
    "pour confirmer une maitrise complete,",
]
TOPICS = [
    "fondamentaux",
    "probabilites_statistiques",
    "donnees",
    "feature_engineering",
    "regression_classification",
    "algorithmes",
    "apprentissage_non_supervise",
    "deep_learning",
    "evaluation",
    "mlops",
]


def category_label(category: str) -> str:
    if category not in CATEGORIES:
        raise ValueError("category_out_of_range")
    return category


def _bp(question: str, choices: list[str], correct_index: int, explanation: str) -> dict:
    return {
        "question": question,
        "choices": choices,
        "correct_index": correct_index,
        "explanation": explanation,
    }


def _unique_question_text(base_question: str, category: str, level: int) -> str:
    category_prompt = CATEGORY_PROMPTS[category]
    level_prompt = LEVEL_PROMPTS[level - 1]
    return f"{category_prompt} {level_prompt} {base_question}"


TOPIC_BLUEPRINTS: dict[str, list[dict]] = {
    "fondamentaux": [
        _bp("Quelle proposition décrit le mieux le machine learning supervisé ?", ["Apprendre à partir d'exemples étiquetés", "Regrouper sans labels", "Compresser des données", "Indexer un texte"], 0, "Le supervisé apprend à partir de labels connus."),
        _bp("Le non supervisé sert surtout à :", ["Prédire une cible connue", "Découvrir des structures sans labels", "Calculer la latence", "Remplacer le pipeline"], 1, "Le non supervisé cherche des structures sans étiquettes."),
        _bp("L'overfitting correspond à :", ["Un modèle trop simple", "Un modèle qui généralise trop bien", "Un modèle qui mémorise le train", "Un modèle sans bruit"], 2, "Le surapprentissage retient trop les détails du train."),
        _bp("Quel compromis est décrit par bias-variance ?", ["Batch et vitesse", "Erreur systématique et sensibilité aux données", "Précision et rappel", "CPU et GPU"], 1, "Le biais reflète la simplification, la variance la sensibilité."),
        _bp("Pourquoi applique-t-on une regularisation ?", ["Augmenter le dataset", "Limiter l'overfitting", "Supprimer les labels", "Rendre les variables continues"], 1, "La régularisation contraint le modèle."),
        _bp("Quelle est la difference entre feature et label ?", ["Entrée et cible", "Texte et image", "Stockage et calcul", "Il n'y a pas de différence"], 0, "Les features sont les entrées, le label est la cible."),
        _bp("Un train/test split sert principalement à :", ["Tout entraîner sur tout", "Mesurer la généralisation", "Créer des données synthétiques", "Accélérer l'inférence"], 1, "Le test évalue des données jamais vues."),
        _bp("Quel algorithme met souvent à jour les poids par petites étapes ?", ["Gradient descent", "K-means", "Apriori", "PCA"], 0, "La descente de gradient ajuste les paramètres progressivement."),
        _bp("Pourquoi garder un baseline est utile ?", ["Servir de référence minimale", "Empêcher toute amélioration", "Faire du clustering", "Transformer les labels"], 0, "Le baseline donne un point de comparaison."),
        _bp("Pourquoi monitorer un modèle après déploiement ?", ["Vérifier sa stabilité", "Supprimer les métriques", "Éviter les logs", "Remplacer le retraining"], 0, "Le monitoring détecte dérives et incidents."),
    ],
    "evaluation": [
        _bp("Quand les classes sont très déséquilibrées, quelle métrique est souvent plus informative que l'accuracy ?", ["F1-score", "MSE", "R2", "Silhouette score"], 0, "Le F1 combine précision et rappel."),
        _bp("La précision mesure :", ["Vrais positifs parmi les prédictions positives", "Vrais positifs parmi les positifs réels", "Erreur au carré", "Séparation inter-clusters"], 0, "La précision mesure la fiabilité des positifs prédits."),
        _bp("Le rappel mesure :", ["Vrais positifs parmi les prédictions positives", "Vrais positifs parmi les positifs réels", "La moyenne des prédictions", "La stabilité du pipeline"], 1, "Le rappel mesure la couverture des positifs réels."),
        _bp("Le F1-score combine principalement :", ["Précision et rappel", "Accuracy et latence", "R2 et MSE", "AUC et temps de réponse"], 0, "Le F1 est la moyenne harmonique de précision et rappel."),
        _bp("ROC-AUC résume :", ["La courbe précision-rappel uniquement", "La capacité à séparer les classes sur tous les seuils", "Le temps d'entraînement", "La mémoire utilisée"], 1, "ROC-AUC mesure la séparation globale entre classes."),
        _bp("PR-AUC est souvent préférable quand :", ["Les classes sont équilibrées", "La classe positive est rare", "On fait de la régression", "On ne possède aucun label"], 1, "PR-AUC est plus sensible à la classe minoritaire."),
        _bp("Quel est l'objectif principal de la validation croisée ?", ["Estimer la performance plus robustement", "Créer des labels", "Augmenter le dataset", "Supprimer les outliers"], 0, "La cross-validation stabilise l'estimation."),
        _bp("Une matrice de confusion permet de :", ["Voir TP, FP, TN, FN", "Mesurer la latence", "Calculer le nombre de features", "Créer des clusters"], 0, "Elle détaille les bonnes et mauvaises classifications."),
        _bp("La calibration d'un modèle concerne :", ["La correspondance entre probabilité et fréquence réelle", "Le choix d'un GPU", "La fenêtre de logs", "Le nombre de clusters"], 0, "Une bonne calibration rend les probabilités fiables."),
        _bp("Le jeu de test doit servir surtout à :", ["Ajuster les hyperparamètres", "Mesurer la performance finale", "Nettoyer les données", "Faire du feature engineering interactif"], 1, "Le test sert à l'évaluation finale."),
    ],
    "donnees": [
        _bp("Quelle situation correspond à une data leakage ?", ["Scaler appris sur train uniquement", "Variable future indisponible en production", "Retirer une colonne constante", "Supprimer les doublons"], 1, "La fuite survient quand une info du futur entre dans l'entraînement."),
        _bp("Quel prétraitement est souvent nécessaire avant KNN ?", ["Standardiser les features", "Supprimer toutes les colonnes numériques", "Transformer le problème en clustering", "Encoder la cible en texte"], 0, "KNN dépend des distances, donc de l'échelle."),
        _bp("Que fait généralement l'imputation ?", ["Remplacer ou estimer les valeurs manquantes", "Créer des labels supplémentaires", "Réduire le nombre de classes", "Supprimer le besoin de validation"], 0, "L'imputation traite les valeurs absentes."),
        _bp("Quelle technique est adaptée aux variables catégorielles nominales ?", ["One-hot encoding", "Normalisation min-max", "PCA avant encodage", "Bootstrap des labels"], 0, "One-hot transforme chaque catégorie en indicateur binaire."),
        _bp("Pourquoi surveiller les outliers ?", ["Ils peuvent perturber des modèles", "Ils suppriment le bruit", "Ils garantissent une meilleure calibration", "Ils remplacent les features manquantes"], 0, "Les valeurs extrêmes influencent fortement certaines statistiques."),
        _bp("Quel problème aide à traiter la déduplication ?", ["Les doublons qui biaisent l'apprentissage", "Les clusters trop compacts", "Les cibles numériques", "Les GPU trop lents"], 0, "Les doublons peuvent sur-pondérer des exemples."),
        _bp("En séries temporelles, il faut privilégier :", ["Un split aléatoire", "Un split chronologique", "Une cible one-hot", "Un clustering"], 1, "Le futur ne doit jamais fuiter."),
        _bp("La feature engineering consiste à :", ["Créer ou transformer des variables utiles", "Supprimer tous les labels", "Éviter tout prétraitement", "Rendre les données non structurées"], 0, "Elle améliore la représentation des données."),
        _bp("Pourquoi surveiller la qualité des données en production ?", ["Détecter anomalies et dérives", "Rendre la base plus petite", "Augmenter l'accuracy artificiellement", "Éviter de versionner les schémas"], 0, "Les variations de schéma ou de distribution peuvent casser un modèle."),
        _bp("Un bon pipeline de données doit surtout être :", ["Reproductible et traçable", "Opaque et manuel", "Dépendant d'un seul fichier local", "Sans monitoring"], 0, "La traçabilité facilite debug et audit."),
    ],
    "probabilites_statistiques": [
        _bp("En probabilité, une variable aléatoire représente surtout :", ["Une quantité numérique incertaine", "Une colonne supprimée", "Un type de GPU", "Un fichier de logs"], 0, "Une variable aléatoire modélise une valeur incertaine."),
        _bp("L'espérance mathématique d'une variable correspond à :", ["Sa valeur moyenne théorique", "Son maximum observé", "Sa variance", "Sa médiane uniquement"], 0, "L'espérance est la moyenne pondérée par les probabilités."),
        _bp("La variance mesure principalement :", ["La dispersion autour de la moyenne", "Le nombre de classes", "Le temps d'inférence", "Le taux d'apprentissage"], 0, "La variance quantifie l'étalement des valeurs."),
        _bp("Un intervalle de confiance à 95 % sert surtout à :", ["Estimer une plage plausible pour un paramètre", "Garantir 95 % d'accuracy", "Éviter toute erreur de mesure", "Choisir un optimiseur"], 0, "Il fournit une plage plausible pour le paramètre estimé."),
        _bp("En test d'hypothèse, la p-value est :", ["La probabilité d'observer des données aussi extrêmes sous H0", "La précision du modèle", "Le rappel moyen", "Le nombre de folds"], 0, "La p-value évalue la compatibilité des données avec H0."),
        _bp("La loi normale est importante car :", ["Beaucoup de phénomènes agrégés s'en approchent", "Elle remplace les labels", "Elle force un modèle linéaire", "Elle supprime le bruit"], 0, "Par le théorème central limite, de nombreuses moyennes tendent vers une normale."),
        _bp("Le score z sert à :", ["Standardiser une valeur par rapport à la moyenne et à l'écart-type", "Compresser des images", "Mesurer la latence", "Classer des textes"], 0, "Le z-score mesure l'écart en nombre d'écarts-types."),
        _bp("En ML, pourquoi faire de l'échantillonnage stratifié ?", ["Préserver la proportion des classes", "Augmenter artificiellement le F1", "Éviter tout overfitting", "Supprimer les outliers"], 0, "Le stratifié garde une distribution de classes proche."),
        _bp("Le biais d'échantillonnage provoque surtout :", ["Des estimations non représentatives", "Des modèles plus rapides", "Une baisse de mémoire", "Une meilleure calibration"], 0, "Un échantillon non représentatif fausse les conclusions."),
        _bp("Pourquoi connaître Bayes en classification ?", ["Pour mettre à jour une probabilité avec de nouvelles évidences", "Pour supprimer les variables", "Pour régler le batch size", "Pour visualiser les clusters"], 0, "Bayes relie prior, vraisemblance et posterior."),
    ],
    "feature_engineering": [
        _bp("Le feature engineering consiste surtout à :", ["Concevoir des variables qui facilitent l'apprentissage", "Changer l'algorithme sans toucher aux données", "Supprimer la cible", "Ignorer les valeurs manquantes"], 0, "De meilleures variables simplifient la tâche du modèle."),
        _bp("Pourquoi encoder les catégories rares explicitement ?", ["Limiter le bruit et la fragmentation", "Augmenter la taille du test", "Supprimer la validation", "Forcer un modèle non linéaire"], 0, "Regrouper les catégories rares peut stabiliser le modèle."),
        _bp("Le scaling est important quand :", ["Le modèle repose sur des distances ou des gradients", "On utilise uniquement des règles métier", "La cible est textuelle", "On n'a aucune feature numérique"], 0, "KNN, SVM et réseaux de neurones sont sensibles à l'échelle."),
        _bp("Un encodage target doit être appliqué avec prudence pour éviter :", ["La fuite de données", "Le sous-apprentissage systématique", "La réduction de dimension", "La sérialisation du modèle"], 0, "Un target encoding mal validé peut fuiter la cible."),
        _bp("Pourquoi créer des interactions entre variables ?", ["Capturer des effets combinés", "Réduire toutes les corrélations à zéro", "Supprimer le besoin de régularisation", "Éviter toute sélection de variables"], 0, "Certaines relations émergent seulement via des combinaisons."),
        _bp("La discrétisation d'une variable continue peut aider à :", ["Rendre certains motifs non linéaires plus lisibles", "Augmenter la précision machine", "Supprimer les outliers automatiquement", "Éviter le split train/test"], 0, "Le binning peut simplifier certaines relations."),
        _bp("La sélection de variables sert principalement à :", ["Conserver les variables informatives", "Ajouter du bruit", "Dupliquer le dataset", "Remplacer l'évaluation"], 0, "Elle réduit le bruit, le coût et le risque de surapprentissage."),
        _bp("En texte, une approche classique de features est :", ["TF-IDF", "Min-max sur labels", "One-hot des epochs", "Batch normalization"], 0, "TF-IDF transforme les mots en poids informatifs."),
        _bp("En dates, une transformation utile est :", ["Extraire jour, mois, heure, cyclicité", "Supprimer toutes les dates", "Transformer en image", "Encoder en labels aléatoires"], 0, "Les attributs temporels explicites aident beaucoup de modèles."),
        _bp("Pourquoi versionner le pipeline de features ?", ["Garantir la même transformation en train et en production", "Éviter les tests", "Supprimer la reproductibilité", "Remplacer le monitoring"], 0, "La cohérence train/production est critique."),
    ],
    "regression_classification": [
        _bp("La régression vise principalement à prédire :", ["Une valeur continue", "Une catégorie discrète uniquement", "Un cluster", "Un score de latence"], 0, "La régression cible des valeurs numériques."),
        _bp("La classification vise principalement à prédire :", ["Une classe ou étiquette", "Une variable continue", "Une composante principale", "Une base de données"], 0, "La classification assigne une catégorie."),
        _bp("Pour évaluer une régression, on utilise souvent :", ["MAE ou RMSE", "Précision et rappel", "Silhouette", "ROC uniquement"], 0, "MAE et RMSE sont des métriques standard de régression."),
        _bp("Pour évaluer une classification binaire, on utilise souvent :", ["Précision, rappel, F1", "MAE et MAPE", "R2 uniquement", "Davies-Bouldin"], 0, "Ces métriques capturent les erreurs de classes."),
        _bp("Une frontière de décision linéaire signifie :", ["La séparation des classes suit une relation linéaire", "Le modèle est non supervisé", "Le modèle n'a pas de biais", "La donnée est déjà propre"], 0, "La décision est basée sur une combinaison linéaire des features."),
        _bp("Le threshold en classification sert à :", ["Convertir une probabilité en classe", "Choisir la taille du dataset", "Régler l'optimiseur", "Mesurer la latence"], 0, "Le seuil détermine la classe prédite."),
        _bp("Le class imbalance en classification peut être traité par :", ["Pondération des classes ou rééchantillonnage", "Suppression des labels minoritaires", "Arrêt des validations", "Réduction du nombre de features à 1"], 0, "Le rééquilibrage évite de ne prédire que la classe majoritaire."),
        _bp("L'overfitting en régression se voit souvent par :", ["Erreur train faible mais erreur test élevée", "Erreur train et test identiques et élevées", "Temps d'inférence faible", "Variance nulle"], 0, "Le modèle mémorise le train mais généralise mal."),
        _bp("Le sous-apprentissage (underfitting) correspond à :", ["Un modèle trop simple pour le signal", "Un modèle trop profond uniquement", "Une fuite de données", "Une mauvaise sérialisation"], 0, "Le modèle ne capture pas la structure utile."),
        _bp("Dans un pipeline, pourquoi distinguer régression et classification ?", ["Le type de cible guide métriques, pertes et modèles", "Pour économiser le stockage", "Pour éviter toute validation", "Pour supprimer les prétraitements"], 0, "Le choix de la tâche oriente tout le protocole d'apprentissage."),
    ],
    "algorithmes": [
        _bp("Quelle affirmation est correcte à propos de la régression logistique ?", ["Elle prédit uniquement des valeurs continues", "Elle produit une probabilité pour la classe positive", "Elle est non supervisée", "Elle ne nécessite jamais de prétraitement"], 1, "La régression logistique renvoie un score probabiliste."),
        _bp("Un random forest est surtout :", ["Un ensemble d'arbres sur sous-échantillons", "Une compression de données", "Un CNN", "Une réduction de dimension"], 0, "La forêt aléatoire agrège plusieurs arbres."),
        _bp("Un SVM cherche principalement à :", ["Maximiser la marge entre classes", "Réduire la taille du dataset", "Remplacer les labels", "Faire du clustering hiérarchique"], 0, "Le SVM maximise la marge."),
        _bp("KNN classe un point en fonction :", ["De ses plus proches voisins", "De la moyenne globale", "D'un gradient", "D'un arbre profond"], 0, "KNN repose sur la proximité."),
        _bp("Limiter la profondeur d'un arbre de décision aide surtout à :", ["Réduire l'overfitting", "Créer plus de classes", "Augmenter le bruit", "Supprimer la validation croisée"], 0, "Des arbres trop profonds mémorisent le train."),
        _bp("XGBoost appartient à la famille :", ["Des méthodes de boosting", "Des méthodes de clustering", "Des modèles linéaires sans régularisation", "Des algorithmes de compression"], 0, "XGBoost est un booster de gradient."),
        _bp("Naive Bayes repose sur :", ["L'hypothèse d'indépendance conditionnelle", "La maximisation de la marge", "L'optimisation des arbres", "La PCA"], 0, "Le modèle suppose les variables conditionnellement indépendantes."),
        _bp("K-means sert principalement à :", ["Faire du clustering", "Faire de la régression", "Prédire un label binaire", "Compresser des images uniquement"], 0, "K-means regroupe les points autour de centres."),
        _bp("PCA est utile pour :", ["Réduire la dimension en gardant la variance", "Créer des labels", "Faire du boosting", "Remplacer tous les modèles"], 0, "La PCA projette sur des composantes principales."),
        _bp("Sur un réseau de neurones, la regularisation peut aider à :", ["Limiter le surapprentissage", "Supprimer le besoin de données", "Créer des clusters plus compacts", "Rendre l'entraînement inutile"], 0, "La régularisation réduit la capacité à mémoriser."),
    ],
    "apprentissage_non_supervise": [
        _bp("Le clustering sert principalement à :", ["Regrouper des points similaires sans labels", "Prédire une variable continue", "Évaluer une API", "Compresser un modèle"], 0, "Le clustering identifie des groupes naturels."),
        _bp("K-means suppose implicitement des clusters :", ["Plutôt compacts autour de centres", "Toujours non convexes", "Nécessairement de même densité exacte", "Sans outliers"], 0, "K-means fonctionne mieux sur des groupes compacts."),
        _bp("Le choix de k dans K-means peut être guidé par :", ["La méthode du coude", "Le F1-score", "La p-value uniquement", "Le nombre de GPUs"], 0, "La méthode du coude aide à trouver un compromis complexité/performance."),
        _bp("DBSCAN est utile car il peut :", ["Trouver des clusters de forme arbitraire et détecter du bruit", "Exiger k fixe", "Optimiser une régression", "Faire du boosting"], 0, "DBSCAN gère les densités et les outliers."),
        _bp("La réduction de dimension (PCA, UMAP) sert souvent à :", ["Visualiser et compacter l'information", "Créer des labels parfaits", "Supprimer tout bruit", "Remplacer le split train/test"], 0, "Elle facilite l'analyse et parfois l'apprentissage."),
        _bp("Une métrique de qualité de clustering est :", ["Silhouette score", "ROC-AUC", "MAE", "R2"], 0, "La silhouette compare la cohésion intra-cluster et la séparation."),
        _bp("Pourquoi standardiser avant clustering ?", ["Éviter qu'une feature domine les distances", "Augmenter le nombre de labels", "Supprimer les catégories", "Garantir des clusters parfaits"], 0, "Les distances sont sensibles aux échelles."),
        _bp("L'analyse en composantes principales (PCA) est :", ["Une méthode linéaire de projection", "Un algorithme de classification supervisé", "Un modèle de séries temporelles", "Une base de données"], 0, "PCA projette les données sur des axes de variance maximale."),
        _bp("Un autoencoder peut être utilisé en non supervisé pour :", ["Apprendre une représentation compacte", "Mesurer la précision uniquement", "Remplacer tout monitoring", "Évaluer une confusion matrix"], 0, "Les autoencoders apprennent un codage latent."),
        _bp("Le principal risque en non supervisé est :", ["Sur-interpréter des groupes sans validation métier", "Avoir trop de labels", "Ne pas avoir de batch", "Ne pas pouvoir scaler"], 0, "Les groupes trouvés doivent être interprétés avec un contexte métier."),
    ],
    "deep_learning": [
        _bp("Un réseau de neurones profond contient principalement :", ["Plusieurs couches de neurones", "Un seul arbre de décision", "Des clusters fixes", "Une seule règle linéaire"], 0, "La profondeur vient de l'empilement de couches."),
        _bp("La rétropropagation sert à :", ["Calculer les gradients pour mettre à jour les poids", "Générer des labels", "Compresser les images", "Mesurer la latence"], 0, "Backprop transmet l'erreur dans le réseau."),
        _bp("Le rôle du learning rate est de :", ["Contrôler la taille des mises à jour", "Fixer le nombre de classes", "Choisir l'architecture", "Supprimer le besoin de validation"], 0, "Un taux trop grand diverge, trop petit ralentit."),
        _bp("Une fonction d'activation non linéaire permet :", ["D'apprendre des relations complexes", "D'avoir un modèle strictement linéaire", "De supprimer les données", "De remplacer l'optimiseur"], 0, "Sans non-linéarité, le réseau reste linéaire."),
        _bp("Dropout est une technique de :", ["Régularisation", "Normalisation des labels", "Versioning", "Compression sans perte"], 0, "Dropout désactive aléatoirement des neurones à l'entraînement."),
        _bp("Batch normalization aide surtout à :", ["Stabiliser et accélérer l'entraînement", "Augmenter le nombre de classes", "Supprimer la loss", "Éviter le split test"], 0, "Elle normalise les activations intermédiaires."),
        _bp("Un CNN est particulièrement adapté à :", ["Images et signaux spatiaux", "Tableaux SQL", "Clustering de texte uniquement", "Séries de logs sans structure"], 0, "Les convolutions exploitent la structure locale."),
        _bp("Un Transformer est devenu central pour :", ["Le traitement de séquences (texte, multimodal)", "La gestion des index SQL", "La calibration des capteurs", "Le chiffrement des données"], 0, "Les mécanismes d'attention capturent les dépendances longues."),
        _bp("Early stopping sert à :", ["Arrêter l'entraînement avant surapprentissage", "Augmenter la taille du réseau", "Supprimer la validation", "Remplacer l'inférence"], 0, "On arrête quand la validation ne s'améliore plus."),
        _bp("Pourquoi utiliser un GPU en deep learning ?", ["Accélérer les calculs matriciels parallèles", "Éviter toute erreur de données", "Remplacer l'optimisation", "Supprimer les hyperparamètres"], 0, "Le calcul parallèle des tenseurs est bien adapté aux GPU."),
    ],
    "mlops": [
        _bp("Le concept drift correspond à :", ["Un changement de la relation entre features et cible", "Un changement de RAM", "Une erreur CSV", "Une absence de labels"], 0, "Le concept drift touche le mapping entrée-sortie."),
        _bp("Quel est l'objectif principal d'un monitoring modèle en production ?", ["Détecter dérives, dégradations et incidents", "Rendre l'entraînement plus rapide", "Supprimer les logs", "Éviter la validation finale"], 0, "Le monitoring suit qualité, drift et latence."),
        _bp("Le versioning d'un modèle permet surtout de :", ["Revenir à un état connu et auditable", "Supprimer la gouvernance", "Éviter les tests", "Faire du clustering"], 0, "Le versioning facilite le rollback et l'audit."),
        _bp("CI/CD pour un modèle ML sert à :", ["Automatiser tests, packaging et déploiements", "Remplacer les données", "Supprimer la surveillance", "Créer des labels à la volée"], 0, "L'automatisation réduit les erreurs manuelles."),
        _bp("Le rollback est utile lorsqu'il faut :", ["Revenir rapidement à une version stable", "Ajouter des features aléatoires", "Ignorer les incidents", "Augmenter la taille des logs"], 0, "Un rollback restaure une version de référence."),
        _bp("Batch inference signifie que :", ["Les prédictions sont faites par lots", "Le modèle ne doit jamais être versionné", "Les features sont toujours numériques", "La latence n'a pas d'importance"], 0, "Le batch traite un ensemble de requêtes en une passe planifiée."),
        _bp("La latence est particulièrement critique quand :", ["L'application est temps réel", "Le modèle est non supervisé", "Il n'y a pas de monitoring", "Le dataset est trop petit"], 0, "Les usages temps réel demandent des réponses rapides."),
        _bp("Pourquoi retrainer un modèle ?", ["Pour s'adapter à de nouvelles données ou dérives", "Pour supprimer les métriques", "Pour ralentir le système", "Pour éviter la validation croisée"], 0, "Le retraining maintient la qualité quand les données évoluent."),
        _bp("Pourquoi les alertes sont-elles importantes ?", ["Elles signalent rapidement les anomalies", "Elles remplacent les données", "Elles garantissent le F1-score", "Elles suppriment le besoin de logs"], 0, "Les alertes réduisent le temps de réaction."),
        _bp("Une bonne pratique MLOps est de rendre les expériences :", ["Reproductibles", "Aléatoires et non documentées", "Dépendantes d'un seul poste", "Non versionnées"], 0, "La reproductibilité est centrale."),
    ],
}


@dataclass
class Question:
    qid: str
    topic: str
    category: str
    level: int
    question: str
    choices: list[str]
    correct_index: int
    explanation: str


class QuestionBank:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or QUESTION_BANK_PATH
        self._questions = self._generate_questions()

    def _generate_questions(self) -> list[Question]:
        out: list[Question] = []
        seen_texts: set[str] = set()
        for category in CATEGORIES:
            for level in range(1, LEVELS_PER_CATEGORY + 1):
                for topic, templates in TOPIC_BLUEPRINTS.items():
                    for index, template in enumerate(templates, start=1):
                        question_text = _unique_question_text(
                            base_question=str(template["question"]),
                            category=category,
                            level=level,
                        )
                        if question_text in seen_texts:
                            raise ValueError("duplicate_question_text_generated")
                        seen_texts.add(question_text)
                        out.append(
                            Question(
                                qid=f"{topic}-{category}-l{level:02d}-q{index:02d}",
                                topic=topic,
                                category=category,
                                level=level,
                                question=question_text,
                                choices=list(template['choices']),
                                correct_index=int(template['correct_index']),
                                explanation=str(template['explanation']),
                            )
                        )
        return out

    def questions_for(self, topic: str | None = None, category: str | None = None, level: int | None = None) -> list[Question]:
        pool = self._questions
        if topic:
            pool = [q for q in pool if q.topic == topic]
        if category:
            pool = [q for q in pool if q.category == category]
        if level is not None:
            pool = [q for q in pool if q.level == level]
        return list(pool)

    def sample(self, count: int, topic: str | None = None, category: str | None = None, level: int | None = None) -> list[Question]:
        if level is not None and category is None:
            raise ValueError("category_required_for_level")
        if category is not None and level is None:
            raise ValueError("level_required_for_category")

        pool = self.questions_for(topic=topic, category=category, level=level)
        if not pool:
            raise ValueError("No questions match the requested filters")
        if level is not None:
            if len(pool) < QUESTIONS_PER_LEVEL:
                raise ValueError("level_must_have_10_questions")
            return random.sample(pool, k=QUESTIONS_PER_LEVEL)
        pick_count = min(max(1, count), len(pool))
        return random.sample(pool, k=pick_count)

    def topics(self) -> list[str]:
        available = {q.topic for q in self._questions}
        ordered = [topic for topic in TOPICS if topic in available]
        extra = sorted(available.difference(TOPICS))
        return ordered + extra

    def categories(self, topic: str | None = None) -> list[str]:
        if topic:
            return CATEGORIES[:]
        return CATEGORIES[:]

    def levels(self, category: str | None = None, topic: str | None = None) -> list[int]:
        _ = topic
        if category and category not in CATEGORIES:
            raise ValueError("category_out_of_range")
        return list(range(1, LEVELS_PER_CATEGORY + 1))


class QcmSessionStore:
    def __init__(self, bank: QuestionBank) -> None:
        self.bank = bank
        self._lock = Lock()
        self._sessions: dict[str, dict] = {}
        self._progress: dict[str, dict[str, set[int]]] = {}

    def _topic_progress(self, topic: str) -> dict[str, set[int]]:
        return self._progress.setdefault(topic, {})

    def _passed_levels(self, topic: str, category: str) -> set[int]:
        progress = self._topic_progress(topic)
        return progress.setdefault(category, set())

    def category_states(self, topic: str | None = None) -> list[dict]:
        if not topic:
            return [
                {
                    "value": category,
                    "unlocked": category == CATEGORIES[0],
                    "completed": False,
                    "current": category == CATEGORIES[0],
                }
                for category in CATEGORIES
            ]

        progress = self._topic_progress(topic)
        completed_categories = {
            category for category in CATEGORIES if len(progress.get(category, set())) >= LEVELS_PER_CATEGORY
        }
        first_incomplete_index = next(
            (index for index, category in enumerate(CATEGORIES) if category not in completed_categories),
            len(CATEGORIES),
        )
        states: list[dict] = []
        for index, category in enumerate(CATEGORIES):
            completed = category in completed_categories
            unlocked = first_incomplete_index == len(CATEGORIES) or index <= first_incomplete_index
            current = first_incomplete_index < len(CATEGORIES) and index == first_incomplete_index
            states.append(
                {
                    "value": category,
                    "unlocked": unlocked,
                    "completed": completed,
                    "current": current,
                }
            )
        return states

    def level_states(self, topic: str | None = None, category: str | None = None) -> list[dict]:
        if not category:
            raise ValueError("category_required_for_level")
        if category not in CATEGORIES:
            raise ValueError("category_out_of_range")

        if not topic:
            return [
                {
                    "value": level,
                    "unlocked": level == 1,
                    "completed": False,
                    "current": level == 1,
                }
                for level in range(1, LEVELS_PER_CATEGORY + 1)
            ]

        category_state = next(item for item in self.category_states(topic) if item["value"] == category)
        passed_levels = self._passed_levels(topic, category)
        next_level = next((level for level in range(1, LEVELS_PER_CATEGORY + 1) if level not in passed_levels), None)

        states: list[dict] = []
        for level in range(1, LEVELS_PER_CATEGORY + 1):
            completed = level in passed_levels
            if category_state["completed"]:
                unlocked = True
                current = False
            elif category_state["current"]:
                unlocked = level == next_level or completed
                current = level == next_level
            else:
                unlocked = False
                current = False
            states.append(
                {
                    "value": level,
                    "unlocked": unlocked,
                    "completed": completed,
                    "current": current,
                }
            )
        return states

    def _ensure_progression_is_unlocked(self, topic: str | None, category: str | None, level: int | None) -> None:
        if not topic or not category or level is None:
            return
        category_state = next(item for item in self.category_states(topic) if item["value"] == category)
        if not category_state["unlocked"]:
            raise ValueError("category_locked_until_previous_completed")
        level_state = next(item for item in self.level_states(topic, category) if item["value"] == level)
        if not level_state["unlocked"]:
            raise ValueError("level_locked_until_previous_completed")

    def _record_progress_if_perfect(self, session: dict) -> None:
        topic = session.get("topic")
        category = session.get("category")
        level = session.get("level")
        if not topic or not category or level is None:
            return
        if session["index"] < len(session["questions"]):
            return
        if session["score"] != len(session["questions"]):
            return
        self._passed_levels(topic, category).add(int(level))

    def create_session(self, count: int = QUESTIONS_PER_LEVEL, topic: str | None = None, category: str | None = None, level: int | None = None) -> dict:
        self._ensure_progression_is_unlocked(topic=topic, category=category, level=level)
        picked = self.bank.sample(count=count, topic=topic, category=category, level=level)
        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "index": 0,
            "score": 0,
            "answers": [],
            "topic": topic,
            "category": category,
            "level": level,
            "questions": [
                {
                    "id": q.qid,
                    "topic": q.topic,
                    "category": q.category,
                    "level": q.level,
                    "question": q.question,
                    "choices": q.choices,
                    "correct_index": q.correct_index,
                    "explanation": q.explanation,
                }
                for q in picked
            ],
        }
        with self._lock:
            self._sessions[session_id] = session
        return self._public_session_state(session)

    def answer(self, session_id: str, choice_index: int) -> dict:
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError("session_not_found")
            session = self._sessions[session_id]
            idx = session["index"]
            questions = session["questions"]
            if idx >= len(questions):
                raise ValueError("session_already_completed")
            q = questions[idx]
            is_correct = int(choice_index) == int(q["correct_index"])
            if is_correct:
                session["score"] += 1
            session["answers"].append({
                "question_id": q["id"],
                "choice_index": int(choice_index),
                "is_correct": is_correct,
                "correct_index": int(q["correct_index"]),
                "correct_choice": q["choices"][int(q["correct_index"])],
                "explanation": q["explanation"],
                "topic": q["topic"],
                "category": q["category"],
                "level": int(q["level"]),
            })
            session["index"] += 1
            self._record_progress_if_perfect(session)
            return self._public_session_state(session)

    def get(self, session_id: str) -> dict:
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError("session_not_found")
            return self._public_session_state(self._sessions[session_id])

    def _public_session_state(self, session: dict) -> dict:
        idx = session["index"]
        questions = session["questions"]
        done = idx >= len(questions)
        next_question = None
        if not done:
            q = questions[idx]
            next_question = {
                "id": q["id"],
                "topic": q["topic"],
                "category": q["category"],
                "level": q["level"],
                "question": q["question"],
                "choices": q["choices"],
                "position": idx + 1,
                "total": len(questions),
            }
        topic_stats: dict[str, dict[str, int]] = {}
        for a in session["answers"]:
            t = a["topic"]
            if t not in topic_stats:
                topic_stats[t] = {"correct": 0, "total": 0}
            topic_stats[t]["total"] += 1
            if a["is_correct"]:
                topic_stats[t]["correct"] += 1
        return {
            "session_id": session["session_id"],
            "topic": session.get("topic"),
            "category": session.get("category"),
            "level": session.get("level"),
            "completed": done,
            "score": session["score"],
            "answered": len(session["answers"]),
            "total": len(questions),
            "next_question": next_question,
            "last_answer": session["answers"][-1] if session["answers"] else None,
            "category_states": self.category_states(session.get("topic")),
            "level_states": self.level_states(session.get("topic"), session.get("category")) if session.get("category") else None,
            "topic_stats": topic_stats,
        }
