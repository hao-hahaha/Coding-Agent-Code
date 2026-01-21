// SPDX-License-Identifier: Apache-2.0
let localModel;

async function loadLocal() {
  if (!localModel) {
    try {
      const { pipeline } = await import('../lib/bundle.esm.min.js');
      localModel = await pipeline('text-generation', './wasm_llm/');
    } catch (err) {
      localModel = async (p) => `[offline] ${p}`;
    }
  }
  return localModel;
}

export async function chat(prompt) {
  const key = localStorage.getItem('OPENAI_API_KEY');
  if (key) {
    const resp = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${key}`,
      },
      body: JSON.stringify({
        model: 'gpt-3.5-turbo',
        messages: [{ role: 'user', content: prompt }],
      }),
    });
    const data = await resp.json();
    return data.choices[0].message.content.trim();
  }
  const model = await loadLocal();
  const out = await model(prompt);
  return typeof out === 'string' ? out : out[0]?.generated_text?.trim();
}

