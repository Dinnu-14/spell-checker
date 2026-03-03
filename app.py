from flask import Flask, request, jsonify, render_template_string
import json

app = Flask(__name__)

# Dictionary of common English words
DICTIONARY = set([
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
    "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
    "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could",
    "them", "see", "other", "than", "then", "now", "look", "only", "come",
    "its", "over", "think", "also", "back", "after", "use", "two", "how",
    "our", "work", "first", "well", "way", "even", "new", "want", "because",
    "any", "these", "give", "day", "most", "us", "received", "message",
    "hello", "world", "python", "computer", "program", "language", "spell",
    "check", "word", "sentence", "correct", "wrong", "error", "fix",
    "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
    "cat", "house", "school", "student", "teacher", "learn", "study",
    "science", "math", "english", "history", "book", "read", "write",
    "speak", "listen", "understand", "question", "answer", "problem",
    "solution", "algorithm", "distance", "minimum", "edit", "insert",
    "delete", "substitute", "operation", "dynamic", "programming",
    "natural", "processing", "artificial", "intelligence", "machine",
    "learning", "data", "model", "train", "test", "accuracy", "result",
    "input", "output", "function", "class", "method", "variable", "return",
    "print", "import", "from", "flask", "request", "response", "server",
    "client", "browser", "network", "internet", "website", "application",
    "project", "system", "design", "implement", "create", "build", "run",
    "start", "stop", "open", "close", "file", "folder", "path", "name",
    "value", "type", "list", "dict", "tuple", "set", "string", "integer",
    "float", "boolean", "true", "false", "none", "null", "empty", "full",
    "large", "small", "big", "little", "old", "young", "hot", "cold",
    "fast", "slow", "high", "low", "long", "short", "wide", "narrow",
    "happy", "sad", "good", "bad", "beautiful", "ugly", "smart", "dumb",
    "easy", "hard", "simple", "complex", "clear", "dark", "light", "heavy",
    "always", "never", "sometimes", "often", "usually", "rarely", "every",
    "each", "both", "few", "more", "many", "much", "same", "different",
    "next", "last", "first", "second", "third", "great", "little", "own",
    "right", "left", "hand", "eye", "face", "head", "body", "heart",
    "love", "life", "death", "world", "place", "home", "family", "friend",
    "thank", "please", "sorry", "excuse", "welcome", "goodbye", "hello",
    "yes", "no", "maybe", "perhaps", "really", "very", "quite", "too",
    "again", "still", "already", "yet", "soon", "late", "early", "today",
    "tomorrow", "yesterday", "morning", "evening", "night", "week", "month",
    "information", "important", "different", "through", "during", "before",
    "between", "under", "around", "including", "without", "within", "along",
    "following", "across", "behind", "beyond", "toward", "against", "except"
])


def levenshtein_distance(s1, s2):
    """Compute Levenshtein distance and return distance + DP matrix + operations."""
    m, n = len(s1), len(s2)
    
    # Build DP matrix
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # deletion
                    dp[i][j-1],    # insertion
                    dp[i-1][j-1]   # substitution
                )
    
    # Traceback to find operations
    operations = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and s1[i-1] == s2[j-1]:
            operations.append(("match", s1[i-1], s2[j-1]))
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            operations.append(("substitute", s1[i-1], s2[j-1]))
            i -= 1
            j -= 1
        elif j > 0 and dp[i][j] == dp[i][j-1] + 1:
            operations.append(("insert", "", s2[j-1]))
            j -= 1
        else:
            operations.append(("delete", s1[i-1], ""))
            i -= 1
    
    operations.reverse()
    
    return dp[m][n], dp, operations


def find_best_suggestion(word, dictionary, max_distance=3):
    """Find the closest word in dictionary."""
    best_word = None
    best_dist = float('inf')
    
    word_lower = word.lower()
    
    for dict_word in dictionary:
        if abs(len(dict_word) - len(word_lower)) > max_distance:
            continue
        dist, _, _ = levenshtein_distance(word_lower, dict_word)
        if dist < best_dist:
            best_dist = dist
            best_word = dict_word
    
    return best_word, best_dist


def check_sentence(sentence):
    """Check each word in the sentence."""
    words = sentence.split()
    results = []
    
    for word in words:
        # Strip punctuation for checking
        clean_word = ''.join(c for c in word if c.isalpha())
        if not clean_word:
            continue
        
        if clean_word.lower() in DICTIONARY:
            results.append({
                "word": word,
                "status": "correct",
                "suggestion": None,
                "distance": 0,
                "operations": [],
                "dp_matrix": []
            })
        else:
            suggestion, distance = find_best_suggestion(clean_word, DICTIONARY)
            _, dp_matrix, operations = levenshtein_distance(clean_word.lower(), suggestion or "")
            
            # Format dp matrix for display (limit size)
            s1 = clean_word.lower()
            s2 = suggestion or ""
            
            results.append({
                "word": word,
                "clean_word": clean_word,
                "status": "misspelled",
                "suggestion": suggestion,
                "distance": distance,
                "operations": [{"type": op[0], "from": op[1], "to": op[2]} for op in operations],
                "dp_matrix": dp_matrix,
                "s1": s1,
                "s2": s2
            })
    
    return results


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SpellMind — Intelligent Spell Checker</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface2: #1a1a26;
    --border: #2a2a3d;
    --accent: #7c6af7;
    --accent2: #f7a76a;
    --accent3: #6af7c2;
    --text: #e8e8f0;
    --muted: #666688;
    --correct: #6af7c2;
    --wrong: #f76a6a;
    --warn: #f7a76a;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Mono', monospace;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Animated background grid */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: 
      linear-gradient(rgba(124,106,247,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(124,106,247,0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }

  .glow-orb {
    position: fixed;
    width: 500px; height: 500px;
    border-radius: 50%;
    filter: blur(120px);
    pointer-events: none;
    z-index: 0;
    opacity: 0.15;
  }
  .glow-orb.one { background: var(--accent); top: -200px; left: -100px; }
  .glow-orb.two { background: var(--accent2); bottom: -200px; right: -100px; }

  .container {
    position: relative;
    z-index: 1;
    max-width: 900px;
    margin: 0 auto;
    padding: 60px 24px 80px;
  }

  header {
    text-align: center;
    margin-bottom: 60px;
  }

  .badge {
    display: inline-block;
    background: rgba(124,106,247,0.15);
    border: 1px solid rgba(124,106,247,0.3);
    color: var(--accent);
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    padding: 6px 16px;
    border-radius: 100px;
    margin-bottom: 20px;
  }

  h1 {
    font-family: 'Syne', sans-serif;
    font-size: clamp(36px, 6vw, 64px);
    font-weight: 800;
    line-height: 1;
    letter-spacing: -2px;
    background: linear-gradient(135deg, #fff 30%, var(--accent) 70%, var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 12px;
  }

  .subtitle {
    color: var(--muted);
    font-size: 13px;
    letter-spacing: 1px;
  }

  /* Input area */
  .input-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
  }

  .input-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0.6;
  }

  .input-label {
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 12px;
    display: block;
  }

  textarea {
    width: 100%;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--text);
    font-family: 'Syne', sans-serif;
    font-size: 18px;
    font-weight: 600;
    padding: 16px 20px;
    resize: vertical;
    min-height: 100px;
    outline: none;
    transition: border-color 0.2s;
  }

  textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(124,106,247,0.1);
  }

  textarea::placeholder { color: var(--muted); font-weight: 400; }

  .btn-row {
    display: flex;
    gap: 12px;
    margin-top: 16px;
  }

  .btn {
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    letter-spacing: 1px;
    padding: 12px 28px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
    text-transform: uppercase;
  }

  .btn-primary {
    background: var(--accent);
    color: white;
    font-weight: 500;
  }

  .btn-primary:hover {
    background: #9082f9;
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(124,106,247,0.35);
  }

  .btn-secondary {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
  }

  .btn-secondary:hover { color: var(--text); border-color: var(--muted); }

  /* Results */
  .results-header {
    font-family: 'Syne', sans-serif;
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 16px;
  }

  .word-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    position: relative;
    animation: slideIn 0.3s ease forwards;
    opacity: 0;
  }

  @keyframes slideIn {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .word-card.correct { border-left: 3px solid var(--correct); }
  .word-card.misspelled { border-left: 3px solid var(--wrong); }

  .word-top {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .word-original {
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--wrong);
    text-decoration: line-through;
    text-decoration-color: rgba(247,106,106,0.5);
  }

  .word-original.correct-word { color: var(--correct); text-decoration: none; }

  .arrow { color: var(--muted); font-size: 18px; }

  .word-suggestion {
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--correct);
  }

  .distance-badge {
    margin-left: auto;
    background: rgba(247,167,106,0.15);
    border: 1px solid rgba(247,167,106,0.3);
    color: var(--accent2);
    font-size: 11px;
    letter-spacing: 1px;
    padding: 4px 12px;
    border-radius: 100px;
  }

  .correct-badge {
    background: rgba(106,247,194,0.1);
    border: 1px solid rgba(106,247,194,0.2);
    color: var(--correct);
    font-size: 11px;
    letter-spacing: 1px;
    padding: 4px 12px;
    border-radius: 100px;
  }

  /* Operations */
  .ops-section {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
  }

  .ops-label {
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
  }

  .ops-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .op-chip {
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid;
  }

  .op-chip.match {
    background: rgba(106,247,194,0.08);
    border-color: rgba(106,247,194,0.2);
    color: var(--correct);
  }

  .op-chip.substitute {
    background: rgba(247,167,106,0.1);
    border-color: rgba(247,167,106,0.25);
    color: var(--accent2);
  }

  .op-chip.insert {
    background: rgba(124,106,247,0.1);
    border-color: rgba(124,106,247,0.25);
    color: var(--accent);
  }

  .op-chip.delete {
    background: rgba(247,106,106,0.1);
    border-color: rgba(247,106,106,0.25);
    color: var(--wrong);
  }

  /* DP Matrix */
  .matrix-toggle {
    background: none;
    border: 1px solid var(--border);
    color: var(--muted);
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 1px;
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    margin-top: 12px;
    transition: all 0.2s;
    text-transform: uppercase;
  }

  .matrix-toggle:hover { color: var(--text); border-color: var(--muted); }

  .matrix-container {
    margin-top: 14px;
    overflow-x: auto;
    display: none;
  }

  .matrix-container.visible { display: block; }

  table.dp-matrix {
    border-collapse: collapse;
    font-size: 12px;
  }

  .dp-matrix td, .dp-matrix th {
    width: 36px; height: 36px;
    text-align: center;
    border: 1px solid var(--border);
  }

  .dp-matrix th {
    color: var(--accent);
    background: rgba(124,106,247,0.08);
    font-weight: 500;
  }

  .dp-matrix td { color: var(--text); }
  .dp-matrix td.highlight { background: rgba(124,106,247,0.2); color: var(--accent); font-weight: 700; }

  /* Stats bar */
  .stats-bar {
    display: flex;
    gap: 24px;
    padding: 16px 24px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin-bottom: 24px;
    flex-wrap: wrap;
  }

  .stat { display: flex; align-items: center; gap: 8px; }
  .stat-dot { width: 8px; height: 8px; border-radius: 50%; }
  .stat-dot.c { background: var(--correct); }
  .stat-dot.e { background: var(--wrong); }
  .stat-label { font-size: 12px; color: var(--muted); }
  .stat-val { font-size: 12px; color: var(--text); font-weight: 500; }

  .loading {
    text-align: center;
    padding: 40px;
    color: var(--muted);
    font-size: 13px;
    letter-spacing: 2px;
    text-transform: uppercase;
    display: none;
  }

  .loading.active { display: block; }

  .spinner {
    display: inline-block;
    width: 16px; height: 16px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-right: 10px;
    vertical-align: middle;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--muted);
  }

  .empty-icon {
    font-size: 48px;
    display: block;
    margin-bottom: 12px;
    opacity: 0.4;
  }

  .algo-info {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    margin-top: 40px;
    font-size: 12px;
    color: var(--muted);
    line-height: 1.8;
  }

  .algo-info strong { color: var(--accent); font-weight: 500; }
  .algo-info h3 { font-family: 'Syne', sans-serif; color: var(--text); font-size: 14px; margin-bottom: 8px; }
</style>
</head>
<body>
<div class="glow-orb one"></div>
<div class="glow-orb two"></div>

<div class="container">
  <header>
    <div class="badge">NLP · Minimum Edit Distance</div>
    <h1>SpellMind</h1>
    <p class="subtitle">Intelligent Spell Checker using Levenshtein Distance Algorithm</p>
  </header>

  <div class="input-card">
    <span class="input-label">Input Sentence</span>
    <textarea id="inputText" placeholder="Type a sentence with misspelled words…&#10;e.g. I recieved the mesage yesterday"></textarea>
    <div class="btn-row">
      <button class="btn btn-primary" onclick="checkSpelling()">⚡ Analyze</button>
      <button class="btn btn-secondary" onclick="clearAll()">Clear</button>
      <button class="btn btn-secondary" onclick="loadExample()">Load Example</button>
    </div>
  </div>

  <div id="loading" class="loading"><span class="spinner"></span>Computing edit distances…</div>

  <div id="results"></div>

  <div class="algo-info">
    <h3>How it works</h3>
    The <strong>Levenshtein Distance</strong> algorithm computes the minimum number of single-character edits (insertions, deletions, or substitutions) required to transform one word into another.
    Uses <strong>dynamic programming</strong> — builds an (m+1)×(n+1) matrix where each cell represents the edit distance between prefixes.
    Cost: <strong>Insertion = 1 · Deletion = 1 · Substitution = 1</strong>
  </div>
</div>

<script>
  async function checkSpelling() {
    const text = document.getElementById('inputText').value.trim();
    if (!text) return;

    document.getElementById('loading').classList.add('active');
    document.getElementById('results').innerHTML = '';

    try {
      const res = await fetch('/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sentence: text })
      });
      const data = await res.json();
      renderResults(data.results);
    } catch (e) {
      document.getElementById('results').innerHTML = '<p style="color:var(--wrong)">Error connecting to server.</p>';
    }

    document.getElementById('loading').classList.remove('active');
  }

  function renderResults(results) {
    const container = document.getElementById('results');
    if (!results.length) {
      container.innerHTML = '<div class="empty-state"><span class="empty-icon">✓</span>No words to analyze.</div>';
      return;
    }

    const misspelled = results.filter(r => r.status === 'misspelled');
    const correct = results.filter(r => r.status === 'correct');

    let html = `
      <p class="results-header">Analysis Results</p>
      <div class="stats-bar">
        <div class="stat"><div class="stat-dot e"></div><span class="stat-label">Misspelled</span><span class="stat-val">${misspelled.length}</span></div>
        <div class="stat"><div class="stat-dot c"></div><span class="stat-label">Correct</span><span class="stat-val">${correct.length}</span></div>
        <div class="stat"><span class="stat-label">Total Words</span><span class="stat-val">${results.length}</span></div>
      </div>
    `;

    results.forEach((r, idx) => {
      const delay = idx * 0.08;
      if (r.status === 'correct') {
        html += `
          <div class="word-card correct" style="animation-delay:${delay}s">
            <div class="word-top">
              <span class="word-original correct-word">${r.word}</span>
              <span class="correct-badge">✓ Correct</span>
            </div>
          </div>`;
      } else {
        const opsHtml = r.operations.map(op => {
          if (op.type === 'match') return `<span class="op-chip match">= '${op.from}'</span>`;
          if (op.type === 'substitute') return `<span class="op-chip substitute">sub '${op.from}'→'${op.to}'</span>`;
          if (op.type === 'insert') return `<span class="op-chip insert">ins '${op.to}'</span>`;
          if (op.type === 'delete') return `<span class="op-chip delete">del '${op.from}'</span>`;
        }).join('');

        const matrixHtml = buildMatrixHtml(r.dp_matrix, r.s1 || '', r.s2 || '');
        const matId = 'mat_' + idx;

        html += `
          <div class="word-card misspelled" style="animation-delay:${delay}s">
            <div class="word-top">
              <span class="word-original">${r.word}</span>
              <span class="arrow">→</span>
              <span class="word-suggestion">${r.suggestion}</span>
              <span class="distance-badge">Edit Distance = ${r.distance}</span>
            </div>
            <div class="ops-section">
              <div class="ops-label">Edit Operations</div>
              <div class="ops-row">${opsHtml}</div>
              <button class="matrix-toggle" onclick="toggleMatrix('${matId}')">▾ Show DP Matrix</button>
              <div class="matrix-container" id="${matId}">
                ${matrixHtml}
              </div>
            </div>
          </div>`;
      }
    });

    container.innerHTML = html;
  }

  function buildMatrixHtml(matrix, s1, s2) {
    if (!matrix || !matrix.length) return '';
    let html = '<table class="dp-matrix"><tr><th></th><th>ε</th>';
    for (let c of s2) html += `<th>${c}</th>`;
    html += '</tr>';
    for (let i = 0; i <= s1.length; i++) {
      html += '<tr>';
      html += i === 0 ? '<th>ε</th>' : `<th>${s1[i-1]}</th>`;
      for (let j = 0; j <= s2.length; j++) {
        const isEnd = (i === s1.length && j === s2.length);
        html += `<td class="${isEnd ? 'highlight' : ''}">${matrix[i][j]}</td>`;
      }
      html += '</tr>';
    }
    html += '</table>';
    return html;
  }

  function toggleMatrix(id) {
    const el = document.getElementById(id);
    el.classList.toggle('visible');
    const btn = el.previousElementSibling;
    btn.textContent = el.classList.contains('visible') ? '▴ Hide DP Matrix' : '▾ Show DP Matrix';
  }

  function clearAll() {
    document.getElementById('inputText').value = '';
    document.getElementById('results').innerHTML = '';
  }

  function loadExample() {
    document.getElementById('inputText').value = 'I recieved the mesage and replyed immediatly';
  }

  document.getElementById('inputText').addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.ctrlKey) checkSpelling();
  });
</script>
</body>
</html>'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/check', methods=['POST'])
def check():
    data = request.get_json()
    sentence = data.get('sentence', '')
    results = check_sentence(sentence)
    return jsonify({"results": results})


if __name__ == '__main__':
    print("=" * 50)
    print("  SpellMind — Intelligent Spell Checker")
    print("  NLP · Minimum Edit Distance")
    print("=" * 50)
    print("  Open your browser: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)