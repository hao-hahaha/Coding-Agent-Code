// SPDX-License-Identifier: Apache-2.0
export async function loadExamples(url = './data/critics/innovations.txt') {
  try {
    const res = await fetch(url);
    if (!res.ok) return [];
    const text = await res.text();
    return text.split(/\n/).map(l => l.trim()).filter(Boolean);
  } catch {
    return [];
  }
}

export class LogicCritic {
  constructor(examples = []) {
    this.examples = examples;
    this.index = {};
    this.examples.forEach((e, i) => {
      this.index[e.toLowerCase()] = i;
    });
    this.scale = Math.max(this.examples.length - 1, 1);
  }

  score(genome) {
    const key = String(genome).toLowerCase();
    const pos = this.index[key] ?? -1;
    const base = pos >= 0 ? (pos + 1) / (this.scale + 1) : 0;
    const noise = Math.random() * 0.001;
    const val = base + noise;
    return Math.min(1, Math.max(0, val));
  }
}

export class FeasibilityCritic {
  constructor(examples = []) {
    this.examples = examples;
  }

  static jaccard(a, b) {
    const sa = new Set(a);
    const sb = new Set(b);
    if (!sa.size || !sb.size) return 0;
    let inter = 0;
    for (const x of sa) if (sb.has(x)) inter++;
    const union = new Set([...a, ...b]).size;
    return inter / union;
  }

  score(genome) {
    const tokens = String(genome).toLowerCase().split(/\s+/);
    let best = 0;
    for (const ex of this.examples) {
      const sim = FeasibilityCritic.jaccard(tokens, ex.toLowerCase().split(/\s+/));
      if (sim > best) best = sim;
    }
    const noise = Math.random() * 0.001;
    const val = best + noise;
    return Math.min(1, Math.max(0, val));
  }
}
