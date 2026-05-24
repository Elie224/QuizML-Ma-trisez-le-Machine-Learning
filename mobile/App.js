import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

const API_URL_KEY = 'qcm_api_url';
const DEFAULT_API_URL = 'http://10.0.2.2:8011';

const CATEGORIES = ['facile', 'moyen', 'difficile', 'tres difficile', 'expert'];

function categoryLabel(category) {
  if (!category) return '-';
  return category === 'tres difficile' ? 'très difficile' : category;
}

function topicLabel(topic) {
  if (!topic) return '-';
  const names = {
    fondamentaux: 'Fondamentaux',
    probabilites_statistiques: 'Probabilités et statistiques',
    donnees: 'Données',
    feature_engineering: 'Feature engineering',
    regression_classification: 'Régression et classification',
    algorithmes: 'Algorithmes',
    apprentissage_non_supervise: 'Apprentissage non supervisé',
    deep_learning: 'Deep learning',
    evaluation: 'Évaluation',
    mlops: 'MLOps',
  };
  const levels = {
    fondamentaux: 'Débutant',
    probabilites_statistiques: 'Débutant',
    donnees: 'Débutant',
    feature_engineering: 'Intermédiaire',
    regression_classification: 'Intermédiaire',
    algorithmes: 'Intermédiaire',
    apprentissage_non_supervise: 'Intermédiaire',
    deep_learning: 'Avancé',
    evaluation: 'Avancé',
    mlops: 'Avancé',
  };
  const pretty = names[topic] || topic.replaceAll('_', ' ');
  const level = levels[topic];
  return level ? `${pretty} (${level})` : pretty;
}

async function apiCall(baseUrl, path, options = {}) {
  const res = await fetch(`${baseUrl}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof body?.detail === 'string' ? body.detail : `HTTP ${res.status}`;
    throw new Error(detail);
  }
  return body;
}

function Chip({ active, label, onPress }) {
  return (
    <Pressable onPress={onPress} style={[styles.chip, active && styles.chipActive]}>
      <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
    </Pressable>
  );
}

function ChoiceCard({ index, text, selected, onPress }) {
  return (
    <Pressable onPress={onPress} style={[styles.choiceCard, selected && styles.choiceCardSelected]}>
      <Text style={styles.choiceIndex}>{index + 1}</Text>
      <Text style={styles.choiceText}>{text}</Text>
    </Pressable>
  );
}

export default function App() {
  const [apiUrl, setApiUrl] = useState(DEFAULT_API_URL);
  const [apiUrlDraft, setApiUrlDraft] = useState(DEFAULT_API_URL);
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState('');
  const [category, setCategory] = useState('facile');

  const [session, setSession] = useState(null);
  const [selectedChoice, setSelectedChoice] = useState(null);
  const [feedback, setFeedback] = useState('Prêt.');
  const [leaderboard, setLeaderboard] = useState([]);

  const [loading, setLoading] = useState(false);
  const [booting, setBooting] = useState(true);

  const isCompleted = Boolean(session?.completed);
  const currentQuestion = session?.next_question;
  const progress = useMemo(() => {
    if (!session?.total) return 0;
    return Math.round(((session.answered || 0) / session.total) * 100);
  }, [session]);

  useEffect(() => {
    (async () => {
      const saved = await AsyncStorage.getItem(API_URL_KEY);
      const initial = saved || DEFAULT_API_URL;
      setApiUrl(initial);
      setApiUrlDraft(initial);
      try {
        await Promise.all([loadTopics(initial), loadLeaderboard(initial)]);
      } finally {
        setBooting(false);
      }
    })();
  }, []);

  async function loadTopics(base = apiUrl) {
    const data = await apiCall(base, '/qcm/topics');
    setTopics(data.topics || []);
    if (!selectedTopic && data.topics && data.topics.length) {
      setSelectedTopic(data.topics[0]);
    }
  }

  async function loadLeaderboard(base = apiUrl) {
    const data = await apiCall(base, '/qcm/leaderboard?limit=8');
    setLeaderboard(data.items || []);
  }

  async function saveApiUrl() {
    const trimmed = apiUrlDraft.trim().replace(/\/$/, '');
    if (!trimmed) return;
    setApiUrl(trimmed);
    await AsyncStorage.setItem(API_URL_KEY, trimmed);
    setFeedback('Serveur mis à jour.');
    setSession(null);
    setSelectedChoice(null);
    setLoading(true);
    try {
      await Promise.all([loadTopics(trimmed), loadLeaderboard(trimmed)]);
    } catch (err) {
      setFeedback(`Erreur serveur: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function startSession() {
    setLoading(true);
    setSelectedChoice(null);
    setFeedback('Démarrage de la session...');
    try {
      const payload = {
        topic: selectedTopic || null,
        category,
        count: 10,
      };
      const data = await apiCall(apiUrl, '/qcm/sessions', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      setSession(data);
      setFeedback('Session démarrée.');
    } catch (err) {
      setFeedback(`Erreur: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function submitAnswer() {
    if (!session || selectedChoice === null) {
      setFeedback('Choisis une réponse.');
      return;
    }
    setLoading(true);
    try {
      const data = await apiCall(apiUrl, `/qcm/sessions/${session.session_id}/answer`, {
        method: 'POST',
        body: JSON.stringify({ choice_index: selectedChoice }),
      });
      setSession(data);
      setSelectedChoice(null);
      if (data.last_answer) {
        const prefix = data.last_answer.is_correct ? 'Bonne réponse.' : `Mauvaise réponse. Bonne réponse : ${data.last_answer.correct_index + 1}.`;
        setFeedback(`${prefix} ${data.last_answer.explanation || ''}`.trim());
      }
    } catch (err) {
      setFeedback(`Erreur: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  if (booting) {
    return (
      <SafeAreaView style={styles.bootScreen}>
        <ActivityIndicator size="large" color="#26a269" />
        <Text style={styles.bootText}>Chargement de QCM ML Mobile...</Text>
      </SafeAreaView>
    );
  }

  return (
    <LinearGradient colors={['#f8fdf9', '#e8f7ef', '#d8f0e2']} style={styles.gradient}>
      <SafeAreaView style={styles.safeArea}>
        <StatusBar style="dark" />
        <ScrollView contentContainerStyle={styles.container}>
          <View style={styles.hero}>
            <Text style={styles.heroTitle}>QCM ML Mobile</Text>
            <Text style={styles.heroSub}>Entraînement intelligent, correction instantanée, progression visible.</Text>
            <View style={styles.kpiRow}>
              <View style={styles.kpiCard}><Text style={styles.kpiLabel}>Score</Text><Text style={styles.kpiValue}>{session?.score || 0}/{session?.total || 0}</Text></View>
              <View style={styles.kpiCard}><Text style={styles.kpiLabel}>Question</Text><Text style={styles.kpiValue}>{(session?.answered || 0) + (isCompleted ? 0 : 1)}/{session?.total || 0}</Text></View>
              <View style={styles.kpiCard}><Text style={styles.kpiLabel}>Catégorie</Text><Text style={styles.kpiValue}>{categoryLabel(session?.category || category)}</Text></View>
            </View>
            <View style={styles.progressTrack}><View style={[styles.progressFill, { width: `${progress}%` }]} /></View>
          </View>

          <View style={styles.panel}>
            <Text style={styles.panelTitle}>Serveur API</Text>
            <TextInput value={apiUrlDraft} onChangeText={setApiUrlDraft} style={styles.input} autoCapitalize="none" autoCorrect={false} />
            <Pressable onPress={saveApiUrl} style={styles.secondaryBtn}><Text style={styles.secondaryBtnText}>Mettre à jour</Text></Pressable>
            <Text style={styles.hint}>Android emulator: http://10.0.2.2:8011</Text>
          </View>

          <View style={styles.panel}>
            <Text style={styles.panelTitle}>Configuration session</Text>
            <Text style={styles.label}>Thème</Text>
            <View style={styles.chipWrap}>
              {topics.map((t) => (
                <Chip key={t} label={topicLabel(t)} active={selectedTopic === t} onPress={() => setSelectedTopic(t)} />
              ))}
            </View>

            <Text style={styles.label}>Catégorie</Text>
            <View style={styles.chipWrap}>
              {CATEGORIES.map((item) => (
                <Chip key={item} label={item} active={category === item} onPress={() => setCategory(item)} />
              ))}
            </View>
            <Text style={styles.hint}>Choisis une seule catégorie par session.</Text>

            <Pressable onPress={startSession} disabled={loading} style={styles.primaryBtn}>
              <Text style={styles.primaryBtnText}>{loading ? 'Chargement...' : 'Démarrer la session'}</Text>
            </Pressable>
          </View>

          <View style={styles.panel}>
            <Text style={styles.panelTitle}>Question</Text>
            {!session && <Text style={styles.emptyText}>Lance une session pour voir une question.</Text>}
            {session && isCompleted && <Text style={styles.doneText}>Session terminée. Score final : {session.score}/{session.total}</Text>}
            {session && !isCompleted && currentQuestion && (
              <>
                <Text style={styles.questionMeta}>#{currentQuestion.position}/{currentQuestion.total} - {topicLabel(currentQuestion.topic)} - catégorie {categoryLabel(currentQuestion.category)}</Text>
                <Text style={styles.questionText}>{currentQuestion.question}</Text>
                <View style={styles.choiceWrap}>
                  {currentQuestion.choices.map((choice, idx) => (
                    <ChoiceCard
                      key={`${idx}-${choice}`}
                      index={idx}
                      text={choice}
                      selected={selectedChoice === idx}
                      onPress={() => setSelectedChoice(idx)}
                    />
                  ))}
                </View>
                <Pressable onPress={submitAnswer} disabled={loading} style={styles.primaryBtn}>
                  <Text style={styles.primaryBtnText}>Valider la réponse</Text>
                </Pressable>
              </>
            )}
            <Text style={styles.feedback}>{feedback}</Text>
          </View>

          <View style={styles.panel}>
            <Text style={styles.panelTitle}>Leaderboard</Text>
            {leaderboard.length === 0 && <Text style={styles.emptyText}>Aucun score pour le moment.</Text>}
            {leaderboard.map((item, idx) => (
              <View key={`${item.player}-${idx}`} style={styles.leaderRow}>
                <Text style={styles.leaderRank}>#{idx + 1}</Text>
                <Text style={styles.leaderPlayer}>{item.player}</Text>
                <Text style={styles.leaderScore}>{item.score}/{item.total}</Text>
                <Text style={styles.leaderRatio}>{Math.round((item.ratio || 0) * 100)}%</Text>
              </View>
            ))}
          </View>
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  container: { padding: 16, paddingBottom: 30, gap: 14 },
  bootScreen: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#f2faf5' },
  bootText: { marginTop: 12, color: '#1f4637', fontWeight: '600' },

  hero: {
    borderRadius: 18,
    padding: 16,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#cde8d8',
  },
  heroTitle: { fontSize: 28, fontWeight: '800', color: '#113a2b' },
  heroSub: { marginTop: 4, color: '#3c6352', lineHeight: 20 },
  kpiRow: { flexDirection: 'row', gap: 8, marginTop: 12 },
  kpiCard: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 8,
    backgroundColor: '#edf8f1',
    borderWidth: 1,
    borderColor: '#c8e6d4',
  },
  kpiLabel: { fontSize: 11, textTransform: 'uppercase', color: '#4d7664', fontWeight: '700' },
  kpiValue: { marginTop: 4, fontSize: 15, color: '#113a2b', fontWeight: '700' },
  progressTrack: { marginTop: 10, height: 8, borderRadius: 99, overflow: 'hidden', backgroundColor: '#e1f2e8' },
  progressFill: { height: 8, backgroundColor: '#179966' },

  panel: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#cde8d8',
    padding: 14,
    gap: 8,
  },
  panelTitle: { fontSize: 18, fontWeight: '700', color: '#113a2b' },
  label: { marginTop: 4, fontWeight: '600', color: '#356754' },
  input: {
    borderWidth: 1,
    borderColor: '#c6dfd0',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#f8fcfa',
    color: '#193f31',
  },
  hint: { color: '#5b7f6e', fontSize: 12 },

  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    borderRadius: 999,
    borderWidth: 1,
    borderColor: '#bfdcc9',
    backgroundColor: '#f2faf5',
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  chipActive: {
    backgroundColor: '#dff4e8',
    borderColor: '#22a56c',
  },
  chipText: { color: '#355f4f', fontWeight: '600' },
  chipTextActive: { color: '#0f4f35' },

  primaryBtn: {
    marginTop: 8,
    borderRadius: 12,
    backgroundColor: '#0f7a51',
    paddingVertical: 12,
    alignItems: 'center',
  },
  primaryBtnText: { color: '#ffffff', fontWeight: '700', fontSize: 15 },
  secondaryBtn: {
    borderRadius: 12,
    backgroundColor: '#1c5f8c',
    paddingVertical: 11,
    alignItems: 'center',
  },
  secondaryBtnText: { color: '#ffffff', fontWeight: '700', fontSize: 14 },

  emptyText: { color: '#567667' },
  doneText: { color: '#114d35', fontWeight: '700' },
  questionMeta: { color: '#4f7564', fontWeight: '600', fontSize: 12 },
  questionText: { marginTop: 4, fontSize: 20, lineHeight: 28, color: '#143f30', fontWeight: '700' },
  choiceWrap: { marginTop: 8, gap: 8 },
  choiceCard: {
    flexDirection: 'row',
    gap: 10,
    borderWidth: 1,
    borderColor: '#cbe2d5',
    backgroundColor: '#f8fcfa',
    borderRadius: 12,
    padding: 11,
  },
  choiceCardSelected: {
    borderColor: '#178f5e',
    backgroundColor: '#e5f8ee',
  },
  choiceIndex: {
    width: 24,
    height: 24,
    borderRadius: 12,
    textAlign: 'center',
    textAlignVertical: 'center',
    backgroundColor: '#e6f5ec',
    color: '#195742',
    fontWeight: '700',
  },
  choiceText: { flex: 1, color: '#1d4638', fontWeight: '600' },
  feedback: { marginTop: 6, color: '#1a5a42', lineHeight: 20 },

  leaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e5f1eb',
    paddingVertical: 8,
    gap: 8,
  },
  leaderRank: { width: 34, color: '#3d6756', fontWeight: '700' },
  leaderPlayer: { flex: 1, color: '#173e31', fontWeight: '600' },
  leaderScore: { width: 62, color: '#255c47', fontWeight: '700' },
  leaderRatio: { width: 44, textAlign: 'right', color: '#1b6b4b', fontWeight: '700' },
});