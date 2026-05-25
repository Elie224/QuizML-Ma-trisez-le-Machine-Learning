from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from qcm_engine_fr import QcmSessionStore, QuestionBank
import qcm_leaderboard_fr as leaderboard


app = FastAPI(title="QCM ML API", version="1.0.0")
app.mount("/assets", StaticFiles(directory="data"), name="assets")
bank = QuestionBank()
store = QcmSessionStore(bank)

FRONTEND_HTML = """
<!doctype html>
<html lang="fr">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>QCM ML</title>
    <style>
        :root {
            --bg-0: #ffffff;
            --bg-1: #f5f7fb;
            --ink: #0b0b0c;
            --muted: #4b5563;
            --line: #d1d5db;
            --card: #ffffff;
            --primary: #2563eb;
            --primary-2: #1d4ed8;
            --chip: #f8fafc;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            color: var(--ink);
            font-family: "Segoe UI", "Trebuchet MS", sans-serif;
            background: radial-gradient(circle at 0% 0%, #ffffff 0%, var(--bg-0) 48%, var(--bg-1) 100%);
        }
        .wrap { max-width: 1020px; margin: 26px auto; padding: 0 16px 26px; }
        .hero {
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 20px;
            background: linear-gradient(145deg, #ffffff 0%, #f7f9fc 100%);
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }
        .brand img {
            width: 44px;
            height: 44px;
            border-radius: 10px;
            object-fit: cover;
            border: 1px solid var(--line);
            background: #fff;
        }
        .brand-title {
            font-size: 14px;
            color: var(--muted);
            font-weight: 600;
        }
        h1 { margin: 0; font-size: 30px; letter-spacing: .2px; }
        .sub { margin-top: 6px; color: var(--muted); }
        .grid {
            display: grid;
            grid-template-columns: 1.3fr .7fr;
            gap: 14px;
            margin-top: 14px;
        }
        .card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 16px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }
        .title { font-size: 17px; font-weight: 700; margin-bottom: 10px; }
        .row {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin-bottom: 10px;
        }
        label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
        select, input, button {
            width: 100%;
            padding: 10px;
            border-radius: 10px;
            border: 1px solid var(--line);
            background: #fff;
            font-size: 14px;
        }
        button { cursor: pointer; border: none; color: #fff; font-weight: 600; background: var(--primary); }
        button.alt { background: var(--primary-2); }
        button.ghost { background: #111827; }
        button:disabled { opacity: .5; cursor: not-allowed; }
        .pill {
            display: inline-flex;
            align-items: center;
            border: 1px solid #dbe1ea;
            background: var(--chip);
            border-radius: 999px;
            padding: 7px 12px;
            font-size: 13px;
            margin-right: 6px;
        }
        .meta { color: var(--muted); font-size: 14px; margin: 8px 0; min-height: 22px; }
        .progress-wrap { margin-top: 8px; }
        .progress {
            height: 10px;
            border-radius: 999px;
            background: #e5e7eb;
            overflow: hidden;
        }
        .progress > div {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #2563eb, #1d4ed8);
            transition: width .25s ease;
        }
        .question { font-size: 20px; margin: 10px 0 8px; line-height: 1.4; }
        .choices { display: grid; gap: 9px; margin-top: 8px; }
        .choice {
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 11px;
            cursor: pointer;
            background: #ffffff;
            transition: transform .06s ease, border-color .15s ease;
        }
        .choice:hover { transform: translateY(-1px); border-color: #93c5fd; }
        .choice.selected { border-color: #2563eb; background: #eff6ff; }
        .choice.locked { opacity: .45; cursor: not-allowed; background: #f3f4f6; }
        .choice.done { border-color: #10b981; background: #ecfdf5; }
        .feedback { margin-top: 10px; min-height: 22px; color: #1e3a8a; }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th, td {
            border-bottom: 1px solid #e5e7eb;
            padding: 7px 5px;
            text-align: left;
        }
        th { color: var(--muted); font-weight: 600; }
        .footer-note { margin-top: 10px; font-size: 12px; color: var(--muted); }
        @media (max-width: 900px) {
            .grid { grid-template-columns: 1fr; }
            .row { grid-template-columns: 1fr 1fr; }
        }
    </style>
</head>
<body>
    <div class="wrap">
        <div class="hero">
            <div class="brand">
                <img src="/assets/logo.png" alt="Logo QuizML" />
                <div class="brand-title">QuizML — Maîtrisez le Machine Learning</div>
            </div>
            <h1>QCM Machine Learning</h1>
            <div class="sub">"Les donnees racontent une histoire, le machine learning apprend a l'ecouter."</div>
            <div style="margin-top:10px">
                <span class="pill" id="pillScore">Score: 0/0</span>
                <span class="pill" id="pillQuestion">Question: 0/0</span>
                <span class="pill" id="pillTopic">Thème : -</span>
                <span class="pill" id="pillCategory">Catégorie : -</span>
                <span class="pill" id="pillLevel">Niveau : -</span>
            </div>
        </div>

        <div class="grid">
        <div class="card">
            <div class="title">Session</div>
            <div class="row">
                <div>
                    <label>Thème</label>
                    <select id="topic"></select>
                </div>
                <div>
                    <label>Catégorie</label>
                    <select id="category"></select>
                </div>
                <div>
                    <label>Action</label>
                    <button id="start">Démarrer</button>
                </div>
            </div>
            <p id="meta" class="muted"></p>
            <div class="progress-wrap">
                <div class="progress"><div id="progressFill"></div></div>
            </div>
            <div id="levelsBox" class="choices" style="margin-top:10px"></div>
            <div id="question" class="question"></div>
            <div id="choices" class="choices"></div>
            <p id="feedback" class="feedback"></p>
            <div class="footer-note">Astuce : tu peux changer de thème et de catégorie entre deux sessions pour varier l'entraînement.</div>
        </div>
        </div>
        </div>
    </div>
    <script>
        let session = null;
        let selected = null;
        let answerInFlight = false;
        let selectedLevel = null;
        const $ = (id) => document.getElementById(id);
        const CATEGORIES = ['facile', 'moyen', 'difficile', 'tres difficile', 'expert'];
        const SUCCESS_FEEDBACKS = [
            '🎉 Bravo ! Tu as trouvé la bonne réponse.',
            '✅ Excellent choix ! C\'est la bonne réponse.',
            '🌟 Bien joué ! Tu maîtrises bien cette question.',
            '🚀 Super ! Réponse correcte, tu avances bien.',
            '👏 Très bon réflexe ! La réponse est juste.',
            '💡 Parfait ! Tu as visé juste.',
            '🥳 Réussi ! Tu peux être fier de cette réponse.',
            '🔥 Oui ! C\'est exactement ce qu\'il fallait répondre.',
        ];
        const FAILURE_FEEDBACKS = [
            '💪 Courage ! Ce n\'est pas encore ça.',
            '🙂 Presque ! Tu es sur la bonne voie.',
            '📘 Ce n\'est pas la bonne réponse, mais tu peux progresser.',
            '🧠 Bon essai ! On corrige ça ensemble.',
            '🌱 Ce n\'est pas grave, chaque erreur aide à apprendre.',
            '🔎 Raté pour cette fois, regardons la bonne réponse.',
            '✨ Continue comme ça, tu vas y arriver.',
            '🤝 Essaie encore mentalement avec l\'explication ci-dessous.',
        ];

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

        function setPills(state) {
            if (!state) {
                $('pillScore').textContent = 'Score: 0/0';
                $('pillQuestion').textContent = 'Question: 0/0';
                $('pillTopic').textContent = 'Thème : -';
                $('pillCategory').textContent = 'Catégorie : -';
                $('pillLevel').textContent = 'Niveau : -';
                $('progressFill').style.width = '0%';
                return;
            }
            const answered = Number(state.answered || 0);
            const total = Number(state.total || 0);
            const score = Number(state.score || 0);
            $('pillScore').textContent = `Score: ${score}/${total}`;
            $('pillQuestion').textContent = `Question: ${Math.min(answered + 1, Math.max(total, 1))}/${total}`;
            const topic = state.topic || (state.next_question ? state.next_question.topic : '-');
            $('pillTopic').textContent = `Thème : ${topicLabel(topic)}`;
            const categoryValue = state.category || (state.next_question ? state.next_question.category : null);
            $('pillCategory').textContent = categoryValue ? `Catégorie : ${categoryLabel(categoryValue)}` : 'Catégorie : -';
            const levelValue = state.level || (state.next_question ? state.next_question.level : null);
            $('pillLevel').textContent = levelValue ? `Niveau : ${levelValue}` : 'Niveau : -';
            const progress = total > 0 ? Math.round((answered / total) * 100) : 0;
            $('progressFill').style.width = `${progress}%`;
        }

        function clearWorkArea() {
            $('question').textContent = '';
            $('choices').innerHTML = '';
            $('levelsBox').innerHTML = '';
        }

        function categoryOptionLabel(item) {
            if (item.completed) return `${categoryLabel(item.value)} (terminée)`;
            if (!item.unlocked) return `${categoryLabel(item.value)} (verrouillée)`;
            if (item.current) return `${categoryLabel(item.value)} (en cours)`;
            return categoryLabel(item.value);
        }

        function levelCardLabel(item) {
            if (item.completed) return `Niveau ${item.value} terminé`;
            if (!item.unlocked) return `Niveau ${item.value} verrouillé`;
            if (item.current) return `Niveau ${item.value} à débloquer`;
            return `Niveau ${item.value}`;
        }

        function pickFeedbackMessage(messages, seed) {
            return messages[seed % messages.length];
        }

        async function loadLevels() {
            const params = new URLSearchParams({
                topic: $('topic').value || '',
                category: $('category').value || '',
            });
            const res = await fetch(`/qcm/levels?${params.toString()}`);
            const data = await res.json();
            if (data.detail) {
                $('feedback').textContent = data.detail;
                return;
            }
            const levels = data.levels || [];
            $('levelsBox').innerHTML = '';
            for (const item of levels) {
                const btn = document.createElement('div');
                btn.className = 'choice';
                if (!item.unlocked) {
                    btn.classList.add('locked');
                }
                if (item.completed) {
                    btn.classList.add('done');
                }
                btn.textContent = levelCardLabel(item);
                if (item.unlocked) {
                    btn.onclick = () => startSessionForLevel(item.value);
                }
                $('levelsBox').appendChild(btn);
            }
            $('feedback').textContent = `Choisis un niveau (${levels.length} niveaux). Les niveaux suivants restent verrouillés tant que le précédent n'est pas validé à 100%.`;
        }

        async function startSessionForLevel(level) {
            selectedLevel = level;
            const body = {
                topic: $('topic').value || null,
                category: $('category').value || null,
                level,
                count: 10,
            };
            const res = await fetch('/qcm/sessions', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (data.detail) {
                $('feedback').textContent = data.detail;
                return;
            }
            $('levelsBox').innerHTML = '';
            $('feedback').textContent = `Session démarrée au niveau ${level}.`;
            render(data);
        }

        async function loadTopics() {
            const res = await fetch('/qcm/topics');
            const data = await res.json();
            for (const t of data.topics || []) {
                const opt = document.createElement('option');
                opt.value = t;
                opt.textContent = topicLabel(t);
                $('topic').appendChild(opt);
            }
            if (data.topics && data.topics.length) {
                $('topic').value = data.topics[0];
            }
        }

        async function loadCategories() {
            const params = new URLSearchParams({
                topic: $('topic').value || '',
            });
            const res = await fetch(`/qcm/categories?${params.toString()}`);
            const data = await res.json();
            const categories = data.categories || [];
            $('category').innerHTML = '';
            for (const item of categories) {
                const opt = document.createElement('option');
                opt.value = item.value;
                opt.textContent = categoryOptionLabel(item);
                opt.disabled = !item.unlocked;
                if (item.current) {
                    opt.selected = true;
                }
                $('category').appendChild(opt);
            }
            if (!$('category').value && categories.length) {
                const firstUnlocked = categories.find((item) => item.unlocked);
                if (firstUnlocked) {
                    $('category').value = firstUnlocked.value;
                }
            }
        }

        function render(state) {
            session = state;
            selected = null;
            setPills(state);
            if (!state) return;
            if (state.completed) {
                $('meta').textContent = `Terminée. Score : ${state.score}/${state.total}`;
                $('question').textContent = 'Session terminée.';
                $('choices').innerHTML = '';
                return;
            }
            const q = state.next_question;
            $('meta').textContent = `Niveau ${q.level} | Question ${q.position}/${q.total} | ${topicLabel(q.topic)} | catégorie ${categoryLabel(q.category)}`;
            $('question').textContent = q.question;
            $('choices').innerHTML = '';
            q.choices.forEach((c, i) => {
                const d = document.createElement('div');
                d.className = 'choice';
                d.textContent = `${i + 1}. ${c}`;
                d.onclick = async () => {
                    if (answerInFlight) {
                        return;
                    }
                    selected = i;
                    document.querySelectorAll('.choice').forEach(x => x.classList.remove('selected'));
                    d.classList.add('selected');
                    answerInFlight = true;
                    try {
                        const res = await fetch(`/qcm/sessions/${session.session_id}/answer`, {
                            method: 'POST',
                            headers: {'Content-Type':'application/json'},
                            body: JSON.stringify({choice_index: selected}),
                        });
                        const data = await res.json();
                        if (data.detail) {
                            $('feedback').textContent = data.detail;
                            return;
                        }
                        if (data.last_answer) {
                            const answerSeed = Number(data.answered || 0) + Number(data.score || 0);
                            $('feedback').textContent = data.last_answer.is_correct
                                ? (`${pickFeedbackMessage(SUCCESS_FEEDBACKS, answerSeed)} ${data.last_answer.explanation}`)
                                : (`${pickFeedbackMessage(FAILURE_FEEDBACKS, answerSeed)} La bonne réponse est : ${data.last_answer.correct_choice}. ${data.last_answer.explanation}`);
                        }
                        render(data);
                    } finally {
                        answerInFlight = false;
                    }
                };
                $('choices').appendChild(d);
            });
        }

        $('start').onclick = async () => {
            session = null;
            selected = null;
            selectedLevel = null;
            setPills(null);
            clearWorkArea();
            $('meta').textContent = '';
            await loadLevels();
        };

        $('topic').onchange = async () => {
            await loadCategories();
            $('levelsBox').innerHTML = '';
            $('feedback').textContent = '';
        };

        async function bootstrap() {
            await loadTopics();
            await loadCategories();
        }

        bootstrap();
    </script>
</body>
</html>
"""


class CreateSessionRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=100)
    topic: str | None = None
    category: str | None = None
    level: int | None = Field(default=None, ge=1, le=10)


class AnswerRequest(BaseModel):
    choice_index: int = Field(..., ge=0, le=20)


class LeaderboardSubmitRequest(BaseModel):
    session_id: str = Field(..., min_length=8)
    player: str = Field(default="joueur")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "qcm-ml"}


@app.get("/", response_class=HTMLResponse)
def web_app() -> str:
    return FRONTEND_HTML


@app.get("/qcm/topics")
def list_topics() -> dict[str, list[str]]:
    return {"topics": bank.topics()}


@app.get("/qcm/categories")
def list_categories(topic: str | None = None) -> dict[str, list[dict]]:
    return {"categories": store.category_states(topic=topic)}


@app.get("/qcm/levels")
def list_levels(topic: str | None = None, category: str | None = None) -> dict[str, list[dict]]:
    try:
        return {"levels": store.level_states(topic=topic, category=category)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/qcm/sessions")
def create_session(request: CreateSessionRequest) -> dict:
    try:
        return store.create_session(
            count=request.count,
            topic=request.topic,
            category=request.category,
            level=request.level,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/qcm/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    try:
        return store.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session_not_found") from exc


@app.post("/qcm/sessions/{session_id}/answer")
def answer(session_id: str, request: AnswerRequest) -> dict:
    try:
        return store.answer(session_id=session_id, choice_index=request.choice_index)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session_not_found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/qcm/leaderboard/submit")
def submit_to_leaderboard(request: LeaderboardSubmitRequest) -> dict:
    try:
        state = store.get(request.session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session_not_found") from exc

    if not state.get("completed"):
        raise HTTPException(status_code=400, detail="session_not_completed")

    entry = leaderboard.submit_score(
        player=request.player,
        score=int(state.get("score", 0)),
        total=int(state.get("total", 1)),
    )
    return {"submitted": True, "entry": entry}


@app.get("/qcm/leaderboard")
def get_leaderboard(limit: int = 10) -> dict:
    return {"items": leaderboard.top(limit=limit)}


@app.get("/qcm/leaderboard.csv", response_class=PlainTextResponse)
def get_leaderboard_csv(limit: int = 100) -> str:
    return leaderboard.to_csv(limit=limit)
